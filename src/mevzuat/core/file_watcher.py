"""
File system watcher for monitoring document directories.
"""
import logging
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)

class FileWatcher:
    """Watches directories for file changes and triggers callbacks."""
    
    def __init__(self):
        """Initialize the file watcher."""
        self.observer = Observer()
        self.watched_paths: Dict[str, Set[Callable]] = {}
        self.event_handler = FileChangeHandler(self)
        self.is_running = False
    
    def add_watch(self, path: str, callback: Callable[[str], None]) -> None:
        """
        Add a directory to watch and associate a callback.
        
        Args:
            path: Directory path to watch
            callback: Function to call when files change
        """
        path = str(Path(path).resolve())
        if path not in self.watched_paths:
            self.watched_paths[path] = set()
            if self.is_running:
                self.observer.schedule(self.event_handler, path, recursive=True)
        self.watched_paths[path].add(callback)
    
    def remove_watch(self, path: str, callback: Callable[[str], None]) -> None:
        """
        Remove a watch for a specific path and callback.
        
        Args:
            path: Directory path being watched
            callback: Callback to remove
        """
        path = str(Path(path).resolve())
        if path in self.watched_paths:
            self.watched_paths[path].discard(callback)
            if not self.watched_paths[path]:
                del self.watched_paths[path]
                if self.is_running:
                    for watch in self.observer.get_watched_paths():
                        if watch == path:
                            self.observer.unschedule(watch)
                            break
    
    def start(self) -> None:
        """Start the file watcher."""
        if not self.is_running:
            for path in self.watched_paths:
                self.observer.schedule(self.event_handler, path, recursive=True)
            self.observer.start()
            self.is_running = True
            logger.info("File watcher started")
    
    def stop(self) -> None:
        """Stop the file watcher."""
        if self.is_running:
            self.observer.stop()
            self.observer.join()
            self.is_running = False
            logger.info("File watcher stopped")
    
    def handle_event(self, event: FileSystemEvent) -> None:
        """
        Handle a filesystem event.
        
        Args:
            event: Filesystem event that occurred
        """
        if not event.is_directory and event.event_type in ('created', 'modified'):
            path = str(Path(event.src_path).resolve())
            for watch_path, callbacks in self.watched_paths.items():
                if path.startswith(watch_path):
                    for callback in callbacks:
                        try:
                            callback(path)
                        except Exception as e:
                            logger.error(f"Error in file watch callback for {path}: {e}")


class FileChangeHandler(FileSystemEventHandler):
    """Handler for filesystem change events."""
    
    def __init__(self, watcher: 'FileWatcher'):
        """Initialize with a reference to the parent watcher."""
        self.watcher = watcher
    
    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        self.watcher.handle_event(event)
    
    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        self.watcher.handle_event(event)
