"""
Data persistence layer for Sunset Social
Stores pending and approved ideas in JSON files
"""

import os
import json
from datetime import datetime
from threading import Lock


class DataStore:
    """Thread-safe persistent storage for ideas"""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        self.pending_file = os.path.join(data_dir, 'pending_ideas.json')
        self.approved_file = os.path.join(data_dir, 'approved_ideas.json')
        self.lock = Lock()

        # Ensure directory exists
        os.makedirs(data_dir, exist_ok=True)

    def load_pending(self):
        """Load pending ideas from file"""
        with self.lock:
            if os.path.exists(self.pending_file):
                try:
                    with open(self.pending_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Error loading pending ideas: {e}")
                    return []
            return []

    def load_approved(self):
        """Load approved ideas from file"""
        with self.lock:
            if os.path.exists(self.approved_file):
                try:
                    with open(self.approved_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"Error loading approved ideas: {e}")
                    return []
            return []

    def save_pending(self, ideas):
        """Save pending ideas to file"""
        with self.lock:
            try:
                with open(self.pending_file, 'w', encoding='utf-8') as f:
                    json.dump(ideas, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error saving pending ideas: {e}")

    def save_approved(self, ideas):
        """Save approved ideas to file"""
        with self.lock:
            try:
                with open(self.approved_file, 'w', encoding='utf-8') as f:
                    json.dump(ideas, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"Error saving approved ideas: {e}")

    def add_pending(self, ideas_list, new_ideas):
        """Add new ideas to pending list and persist"""
        ideas_list.extend(new_ideas)
        self.save_pending(ideas_list)

    def approve_idea(self, pending_list, approved_list, idea_id):
        """Move idea from pending to approved"""
        if 0 <= idea_id < len(pending_list):
            idea = pending_list.pop(idea_id)
            idea['status'] = 'approved'
            idea['approved_at'] = datetime.now().isoformat()
            approved_list.append(idea)

            # Persist both lists
            self.save_pending(pending_list)
            self.save_approved(approved_list)
            return idea
        return None

    def reject_idea(self, pending_list, idea_id):
        """Remove idea from pending"""
        if 0 <= idea_id < len(pending_list):
            idea = pending_list.pop(idea_id)
            self.save_pending(pending_list)
            return idea
        return None

    def backup_data(self):
        """Create timestamped backup of current state"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(self.data_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        with self.lock:
            try:
                # Backup pending
                if os.path.exists(self.pending_file):
                    backup_pending = os.path.join(backup_dir, f'pending_{timestamp}.json')
                    with open(self.pending_file, 'r', encoding='utf-8') as src:
                        with open(backup_pending, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())

                # Backup approved
                if os.path.exists(self.approved_file):
                    backup_approved = os.path.join(backup_dir, f'approved_{timestamp}.json')
                    with open(self.approved_file, 'r', encoding='utf-8') as src:
                        with open(backup_approved, 'w', encoding='utf-8') as dst:
                            dst.write(src.read())

                print(f"Backup created: {timestamp}")
            except Exception as e:
                print(f"Error creating backup: {e}")
