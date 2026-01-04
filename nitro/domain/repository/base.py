"""
StarModel Persistence Layer - Base Classes

This module provides abstract interfaces for entity persistence backends.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Optional

class EntityRepositoryInterface(ABC):
    """
    Abstract base class for entity persistence backends.
    
    Implementations must provide methods for saving, loading, and managing
    entity instances with optional TTL support and automatic cleanup.
    """
    
    def __init__(self):
        """Initialize persistence backend with cleanup configuration."""
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_interval: int = 300  # 5 minutes default
        self._auto_cleanup: bool = True
        self._running: bool = False
    
    @abstractmethod
    def save(self, entity, ttl: Optional[int] = None) -> bool:
        """
        Save entity instance to the persistence backend.
        
        Args:
            entity: Entity instance to persist
            ttl: Time-to-live in seconds (optional)
            
        Returns:
            True if save was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def find(self, entity_id: str) -> Optional:
        """
        Load entity instance from the persistence backend.
        
        Args:
            entity_id: Unique identifier for the entity
            
        Returns:
            Entity instance if found, None otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """
        Delete entity from the persistence backend.
        
        Args:
            entity_id: Unique identifier for the entity
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def exists(self, entity_id: str) -> bool:
        """
        Check if entity exists in the persistence backend.
        
        Args:
            entity_id: Unique identifier for the entity
            
        Returns:
            True if entity exists, False otherwise
        """
        pass