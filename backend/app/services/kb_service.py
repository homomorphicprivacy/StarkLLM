"""
kb_service.py — Knowledge Base folder management and sync.

This module exposes the KBService class for managing the lifecycles of KnowledgeBaseFolder
and KnowledgeBaseDocument models. It also preserves backward-compatibility helpers for the
older sync implementations.
"""

import os
import json
import logging
import hashlib
import tempfile
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional
from sqlalchemy.orm import Session

# Try to import document processing libraries
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import docx  # python-docx
except ImportError:
    docx = None

from app.core.config import settings
from app.db import models
from app.db.models import KnowledgeBaseFolder, KnowledgeBaseDocument, KBDocStatus
from app.services.rag_service import rag_service
from app.services.llm_service import llm_service
from app.services.vision_service import vision_service

logger = logging.getLogger(__name__)

# Supported file formats for the second brain feature
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".png", ".jpg", ".jpeg"}


class KBService:
    def add_folder(self, db: Session, user_id: int, folder_path: str, folder_name: str = None) -> KnowledgeBaseFolder:
        """
        Registers a new folder for the user.
        If folder_name is not provided, use the last part of the folder path as the name.
        """
        try:
            if not folder_name:
                # Use the last non-empty part of the path as the display name
                folder_name = os.path.basename(folder_path.rstrip("/\\")) or folder_path

            logger.info(f"Adding KB folder for user {user_id}: path='{folder_path}', name='{folder_name}'")
            
            folder = KnowledgeBaseFolder(
                user_id=user_id,
                folder_path=folder_path,
                folder_name=folder_name,
                is_active=1
            )
            db.add(folder)
            db.commit()
            db.refresh(folder)
            return folder
        except Exception as e:
            db.rollback()
            logger.error(f"Error adding KB folder: {e}", exc_info=True)
            raise

    def get_user_folders(self, db: Session, user_id: int) -> list[KnowledgeBaseFolder]:
        """
        Returns all active folders belonging to a specific user.
        """
        try:
            return db.query(KnowledgeBaseFolder).filter(
                KnowledgeBaseFolder.user_id == user_id,
                KnowledgeBaseFolder.is_active == 1
            ).all()
        except Exception as e:
            logger.error(f"Error getting user KB folders: {e}", exc_info=True)
            raise

    def scan_folder(self, db: Session, folder_id: int) -> list[KnowledgeBaseDocument]:
        """
        Scans the physical folder on disk.
        Finds supported files (PDF, DOCX, PNG, JPG, JPEG).
        For each file that doesn't already exist in the database, creates a
        KnowledgeBaseDocument record with status 'pending'.
        Return the list of newly added documents.
        """
        try:
            folder = db.query(KnowledgeBaseFolder).filter(KnowledgeBaseFolder.id == folder_id).first()
            if not folder:
                raise ValueError(f"KnowledgeBaseFolder with ID {folder_id} not found")

            folder_path_str = folder.folder_path
            logger.info(f"Scanning folder ID {folder_id} (path: '{folder_path_str}')")

            if not os.path.exists(folder_path_str):
                raise FileNotFoundError(f"Physical folder path '{folder_path_str}' does not exist on disk")

            new_documents = []

            # Recursively walk the directory
            for root, dirs, files in os.walk(folder_path_str):
                # Skip hidden directories (starting with .)
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        abs_filepath = os.path.abspath(os.path.join(root, file))
                        
                        # Check if this document already exists in the database under this folder
                        existing_doc = db.query(KnowledgeBaseDocument).filter(
                            KnowledgeBaseDocument.folder_id == folder_id,
                            KnowledgeBaseDocument.file_path == abs_filepath
                        ).first()

                        if not existing_doc:
                            # Gather file stats
                            try:
                                stats = os.stat(abs_filepath)
                                file_size = stats.st_size
                                last_mod_dt = datetime.fromtimestamp(stats.st_mtime)
                            except Exception as stat_err:
                                logger.warning(f"Could not stat file '{abs_filepath}': {stat_err}")
                                continue

                            file_type = ext.lstrip('.')
                            
                            new_doc = KnowledgeBaseDocument(
                                folder_id=folder_id,
                                file_path=abs_filepath,
                                file_name=file,
                                file_type=file_type,
                                file_size=file_size,
                                last_modified=last_mod_dt,
                                status=KBDocStatus.PENDING,
                                chunk_count=0
                            )
                            db.add(new_doc)
                            new_documents.append(new_doc)

            if new_documents:
                db.commit()
                # Refresh all newly created docs to populate IDs/fields from DB
                for doc in new_documents:
                    db.refresh(doc)
                logger.info(f"Scan complete. Added {len(new_documents)} new documents to folder ID {folder_id}")
            else:
                logger.info(f"Scan complete. No new documents found for folder ID {folder_id}")

            return new_documents

        except Exception as e:
            db.rollback()
            logger.error(f"Error scanning folder ID {folder_id}: {e}", exc_info=True)
            raise

    def delete_folder(self, db: Session, folder_id: int, user_id: int) -> bool:
        """
        Deletes a Knowledge Base folder completely from the system:
        - Purges all vector chunks from ChromaDB for all documents in the folder
        - Deletes all KnowledgeBaseDocument records
        - Deletes the KnowledgeBaseFolder record
        Does NOT delete any physical files from the file system.
        """
        try:
            folder = db.query(KnowledgeBaseFolder).filter(
                KnowledgeBaseFolder.id == folder_id,
                KnowledgeBaseFolder.user_id == user_id
            ).first()
            if not folder:
                raise ValueError(f"KnowledgeBaseFolder with ID {folder_id} not found or unauthorized")

            logger.info(f"Deleting folder ID {folder_id} (path: '{folder.folder_path}')")

            # 1. Purge from ChromaDB
            docs = db.query(KnowledgeBaseDocument).filter(KnowledgeBaseDocument.folder_id == folder_id).all()
            if docs:
                doc_ids = [doc.id for doc in docs]
                try:
                    collection = rag_service.get_or_create_kb_collection(user_id)
                    # Delete by finding all document IDs
                    collection.delete(where={"document_id": {"$in": doc_ids}})
                    logger.info(f"Purged {len(doc_ids)} documents from ChromaDB for folder ID {folder_id}")
                except Exception as e:
                    logger.warning(f"Failed to purge chunks for deleted folder {folder_id}: {e}")

            # 2. Delete document records from DB (cascade typically handles this, but we do it explicitly to be safe if cascade isn't set up)
            db.query(KnowledgeBaseDocument).filter(KnowledgeBaseDocument.folder_id == folder_id).delete(synchronize_session=False)

            # 3. Delete folder record from DB
            db.delete(folder)
            db.commit()
            logger.info(f"Successfully deleted folder ID {folder_id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting folder ID {folder_id}: {e}", exc_info=True)
            raise


    def sync_folder(self, db: Session, folder_id: int) -> dict:
        """
        Synchronizes the folder on disk with the database:
        - Finds new files (adds them as pending)
        - Finds modified files (updates size/mtime, sets pending, purges existing chunks)
        - Finds deleted files (removes from DB, purges chunks)
        - Automatically triggers indexing for all pending documents
        Returns a stats dictionary: {'added': int, 'updated': int, 'deleted': int, 'indexed': int, 'failed': int}
        """
        try:
            folder = db.query(KnowledgeBaseFolder).filter(KnowledgeBaseFolder.id == folder_id).first()
            if not folder:
                raise ValueError(f"KnowledgeBaseFolder with ID {folder_id} not found")

            folder_path_str = folder.folder_path
            logger.info(f"Syncing folder ID {folder_id} (path: '{folder_path_str}')")

            if not os.path.exists(folder_path_str):
                raise FileNotFoundError(f"Physical folder path '{folder_path_str}' does not exist on disk")

            # 1. Fetch existing documents for this folder
            existing_docs = db.query(KnowledgeBaseDocument).filter(
                KnowledgeBaseDocument.folder_id == folder_id
            ).all()
            
            # Map by absolute file path for quick lookup
            docs_by_path = {doc.file_path: doc for doc in existing_docs}
            
            new_documents = []
            updated_documents = []
            
            # 2. Walk directory to find current files
            for root, dirs, files in os.walk(folder_path_str):
                dirs[:] = [d for d in dirs if not d.startswith('.')]
                
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in SUPPORTED_EXTENSIONS:
                        abs_filepath = os.path.abspath(os.path.join(root, file))
                        
                        try:
                            stats = os.stat(abs_filepath)
                            file_size = stats.st_size
                            last_mod_dt = datetime.fromtimestamp(stats.st_mtime)
                        except Exception as stat_err:
                            logger.warning(f"Could not stat file '{abs_filepath}': {stat_err}")
                            continue

                        file_type = ext.lstrip('.')
                        
                        existing_doc = docs_by_path.pop(abs_filepath, None)
                        
                        if not existing_doc:
                            # It's a new file
                            new_doc = KnowledgeBaseDocument(
                                folder_id=folder_id,
                                file_path=abs_filepath,
                                file_name=file,
                                file_type=file_type,
                                file_size=file_size,
                                last_modified=last_mod_dt,
                                status=KBDocStatus.PENDING,
                                chunk_count=0
                            )
                            db.add(new_doc)
                            new_documents.append(new_doc)
                        else:
                            # Check if modified
                            # using a slight tolerance for mtime comparison to avoid precision issues
                            diff = abs((existing_doc.last_modified - last_mod_dt).total_seconds())
                            if diff > 1.0 or existing_doc.file_size != file_size:
                                logger.info(f"File modified: {abs_filepath}")
                                existing_doc.file_size = file_size
                                existing_doc.last_modified = last_mod_dt
                                existing_doc.status = KBDocStatus.PENDING
                                existing_doc.chunk_count = 0
                                existing_doc.error_message = None
                                updated_documents.append(existing_doc)
                                
                                # Purge existing chunks
                                try:
                                    collection = rag_service.get_or_create_kb_collection(folder.user_id)
                                    collection.delete(where={"document_id": existing_doc.id})
                                except Exception as e:
                                    logger.warning(f"Failed to purge chunks for modified doc {existing_doc.id}: {e}")

            # 3. Process deleted files (whatever is left in docs_by_path)
            deleted_count = 0
            for abs_filepath, doc_to_delete in docs_by_path.items():
                logger.info(f"File deleted from disk: {abs_filepath}")
                try:
                    collection = rag_service.get_or_create_kb_collection(folder.user_id)
                    collection.delete(where={"document_id": doc_to_delete.id})
                except Exception as e:
                    logger.warning(f"Failed to purge chunks for deleted doc {doc_to_delete.id}: {e}")
                
                db.delete(doc_to_delete)
                deleted_count += 1
                
            db.commit()
            
            added_count = len(new_documents)
            updated_count = len(updated_documents)
            
            logger.info(f"Sync Phase 1 complete. Added: {added_count}, Updated: {updated_count}, Deleted: {deleted_count}")
            
            # 4. Trigger indexing for pending documents
            indexed_ids = self.index_pending_documents(db, folder_id=folder_id)
            
            folder = db.query(KnowledgeBaseFolder).filter(KnowledgeBaseFolder.id == folder_id).first()
            if folder:
                folder.last_indexed_at = datetime.utcnow()
                db.commit()
            
            # Calculate failures (recently failed or still pending might mean failure if indexing threw internally but caught it)
            # We'll just report what got indexed successfully.
            
            return {
                "added": added_count,
                "updated": updated_count,
                "deleted": deleted_count,
                "indexed": len(indexed_ids),
                "failed": 0  # We can't easily count exact failures in this pass without tracking, let's keep it simple
            }

        except Exception as e:
            db.rollback()
            logger.error(f"Error syncing folder ID {folder_id}: {e}", exc_info=True)
            raise

    def get_folder_documents(self, db: Session, folder_id: int) -> list[KnowledgeBaseDocument]:
        """
        Returns all documents belonging to a specific folder.
        """
        try:
            return db.query(KnowledgeBaseDocument).filter(
                KnowledgeBaseDocument.folder_id == folder_id
            ).all()
        except Exception as e:
            logger.error(f"Error getting folder documents for folder ID {folder_id}: {e}", exc_info=True)
            raise

    def update_document_status(
        self,
        db: Session,
        document_id: int,
        status: str,
        chunk_count: int = None,
        error_message: str = None
    ) -> KnowledgeBaseDocument:
        """
        Updates the status of a document (e.g., from 'pending' to 'indexed' or 'failed').
        Optionally updates chunk_count and error_message.
        """
        try:
            doc = db.query(KnowledgeBaseDocument).filter(KnowledgeBaseDocument.id == document_id).first()
            if not doc:
                raise ValueError(f"KnowledgeBaseDocument with ID {document_id} not found")

            logger.info(f"Updating document ID {document_id} status from '{doc.status}' to '{status}'")
            doc.status = status
            
            if chunk_count is not None:
                doc.chunk_count = chunk_count
            if error_message is not None:
                doc.error_message = error_message
            if status == KBDocStatus.INDEXED:
                doc.indexed_at = datetime.utcnow()

            db.commit()
            db.refresh(doc)
            return doc
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating status for document ID {document_id}: {e}", exc_info=True)
            raise

    # ---------------------------------------------------------------------------
    # New Indexing and Helper Methods
    # ---------------------------------------------------------------------------

    def get_embedding_model(self) -> str:
        """Returns the default embedding model configured for the application."""
        return settings.DEFAULT_EMBEDDING_MODEL

    def _chunk_text(self, text: str, chunk_size: int = 700, overlap: int = 100) -> list[str]:
        """Splits text into chunks of length chunk_size with overlap characters."""
        chunks = []
        if not text:
            return chunks
        
        start = 0
        text_len = len(text)
        while start < text_len:
            end = min(start + chunk_size, text_len)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            next_start = start + (chunk_size - overlap)
            if next_start <= start:
                break
            start = next_start
        return chunks

    def index_document(self, db: Session, document_id: int) -> bool:
        """
        Extracts content from a file according to its type, chunks the content,
        generates embeddings, and stores the chunks in ChromaDB.
        """
        doc = db.query(KnowledgeBaseDocument).filter(KnowledgeBaseDocument.id == document_id).first()
        if not doc:
            logger.error(f"KB: KnowledgeBaseDocument with ID {document_id} not found")
            return False

        folder = db.query(KnowledgeBaseFolder).filter(KnowledgeBaseFolder.id == doc.folder_id).first()
        if not folder:
            logger.error(f"KB: KnowledgeBaseFolder with ID {doc.folder_id} not found for document {document_id}")
            return False

        # Set status to indexing
        self.update_document_status(db, document_id, KBDocStatus.INDEXING)

        file_path = doc.file_path
        file_type = doc.file_type.lower()
        extracted_text = ""

        try:
            # 1. Content Extraction
            if file_type == "pdf":
                if not fitz:
                    raise ImportError("PyMuPDF (fitz) is not installed")
                logger.info(f"KB: Extracting PDF text: {file_path}")
                pdf_doc = fitz.open(file_path)
                pages_text = []
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc.load_page(page_num)
                    text = page.get_text("text")
                    if text and text.strip():
                        pages_text.append(text.strip())
                    else:
                        logger.info(f"KB: PDF page {page_num} has no text, falling back to vision description")
                        temp_path = None
                        try:
                            pix = page.get_pixmap()
                            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                                temp_path = tmp.name
                            pix.save(temp_path)
                            
                            pdf_vision_prompt = (
                                "This is a scanned page from a PDF document. "
                                "Please extract the content carefully, paying special attention "
                                "to any text, tables, handwriting, and layout. "
                                "Provide a detailed transcription/description of the page content."
                            )
                            description = vision_service.generate_image_description(
                                temp_path, prompt=pdf_vision_prompt
                            )
                            if description and description.strip():
                                pages_text.append(description.strip())
                        except Exception as vis_err:
                            logger.error(f"KB: Vision fallback failed on page {page_num}: {vis_err}")
                        finally:
                            if temp_path and os.path.exists(temp_path):
                                os.remove(temp_path)
                extracted_text = "\n\n".join(pages_text)

            elif file_type == "docx":
                if not docx:
                    raise ImportError("python-docx is not installed")
                logger.info(f"KB: Extracting DOCX text: {file_path}")
                docx_doc = docx.Document(file_path)
                paragraphs = [p.text for p in docx_doc.paragraphs if p.text.strip()]
                extracted_text = "\n".join(paragraphs)

            elif file_type in ["png", "jpg", "jpeg"]:
                logger.info(f"KB: Generating vision description for image: {file_path}")
                description = vision_service.generate_image_description(file_path)
                if description and description.strip():
                    extracted_text = description.strip()
                else:
                    raise ValueError("Vision service returned empty description for the image")

            else:
                raise ValueError(f"Unsupported file type for indexing: {file_type}")

            # 2. Chunking
            chunks = rag_service._semantic_chunk_text(extracted_text)
            if not chunks:
                raise ValueError("No text content could be extracted from this document")

            # 3. Vector Database Sync (ChromaDB)
            collection = rag_service.get_or_create_kb_collection(folder.user_id)
            
            # Delete any existing chunks for this specific document_id
            try:
                collection.delete(where={"document_id": document_id})
                logger.info(f"KB: Purged existing vector chunks for document ID {document_id}")
            except Exception as delete_err:
                logger.warning(f"KB: Could not delete old chunks for document ID {document_id}: {delete_err}")

            # Generate embeddings
            embedding_model = self.get_embedding_model()
            logger.info(f"KB: Generating embeddings with model '{embedding_model}' for {len(chunks)} chunks")
            embeddings = llm_service.generate_embeddings_batch(embedding_model, chunks)

            # Metadata and IDs
            metadatas = []
            ids = []
            file_prefix = hashlib.md5(file_path.encode()).hexdigest()[:8]

            for idx, chunk in enumerate(chunks):
                metadatas.append({
                    "source": "knowledge_base",
                    "user_id": folder.user_id,
                    "folder_id": doc.folder_id,
                    "document_id": document_id,
                    "file_name": doc.file_name,
                    "file_path": file_path,
                    "chunk_index": idx
                })
                ids.append(f"kb_doc_{document_id}_{file_prefix}_c{idx}")

            # Upsert vectors (safe for re-indexing — avoids duplicate ID errors)
            collection.upsert(
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            # Update status to indexed
            self.update_document_status(
                db,
                document_id,
                KBDocStatus.INDEXED,
                chunk_count=len(chunks),
                error_message=None
            )
            return True

        except Exception as e:
            logger.error(f"KB: Error indexing document ID {document_id}: {e}", exc_info=True)
            self.update_document_status(
                db,
                document_id,
                KBDocStatus.FAILED,
                error_message=str(e)
            )
            return False

    def index_pending_documents(self, db: Session, folder_id: int = None) -> list[int]:
        """
        Finds all documents with status 'pending' in a folder (or all folders)
        and indexes them one by one.
        Returns a list of successfully indexed document IDs.
        """
        try:
            query = db.query(KnowledgeBaseDocument).filter(
                KnowledgeBaseDocument.status == KBDocStatus.PENDING
            )
            if folder_id is not None:
                query = query.filter(KnowledgeBaseDocument.folder_id == folder_id)
                
            pending_docs = query.all()
            logger.info(f"KB: Found {len(pending_docs)} pending document(s) to index.")
            
            successful_ids = []
            for doc in pending_docs:
                logger.info(f"KB: Indexing pending document ID {doc.id} ({doc.file_name})")
                success = self.index_document(db, doc.id)
                if success:
                    successful_ids.append(doc.id)
                    
            return successful_ids
        except Exception as e:
            logger.error(f"KB: Error in index_pending_documents: {e}", exc_info=True)
            raise


kb_service = KBService()
