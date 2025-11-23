from abc import ABC, abstractmethod
from typing import Dict, Any, List

from core.domain import PlaybackState, Session

class IPlayerDriver(ABC):
    """Abstract Base Class for media player drivers."""

    @abstractmethod
    def launch(self, playlist: List[str], start_index: int = 0, start_time: float = 0.0) -> PlaybackState:
        """
        Launches a media player and returns its playback state upon completion or interruption.
        
        Args:
            path (str): The path to the media file.
            start_time (float): The time in seconds to start playback from.
        
        Returns:
            PlaybackState: The final playback state of the media.
        """
        pass

class IRepository(ABC):
    """Abstract Base Class for session data repository."""

    @abstractmethod
    def load_all_sessions(self) -> Dict[str, Session]:
        """
        Loads all stored sessions.
        
        Returns:
            Dict[str, Session]: A dictionary where keys are filepaths and values are Session objects.
        """
        pass

    @abstractmethod
    def save_session(self, session: Session) -> None:
        """
        Saves a single session.
        
        Args:
            session (Session): The session object to save.
        """
        pass

    @abstractmethod
    def delete_session(self, filepath: str) -> None:
        """
        Deletes a session identified by its filepath.
        
        Args:
            filepath (str): The filepath of the session to delete.
        """
        pass
