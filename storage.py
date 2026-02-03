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

    def edit_approved(self, approved_list, idea_id, updates):
        """Edit an approved idea in place"""
        if 0 <= idea_id < len(approved_list):
            idea = approved_list[idea_id]
            idea['titolo'] = updates.get('titolo', idea['titolo'])
            idea['testo_post'] = updates.get('testo_post', idea['testo_post'])
            idea['descrizione'] = updates.get('descrizione', idea['descrizione'])
            idea['media_suggeriti'] = updates.get('media_suggeriti', idea['media_suggeriti'])
            idea['piattaforma'] = updates.get('piattaforma', idea['piattaforma'])
            idea['edited_at'] = datetime.now().isoformat()

            self.save_approved(approved_list)

            # Aggiorna anche il file in post_pronti
            self._update_post_file(idea)
            return idea
        return None

    def delete_approved(self, approved_list, idea_id):
        """Delete an approved idea"""
        if 0 <= idea_id < len(approved_list):
            idea = approved_list.pop(idea_id)
            self.save_approved(approved_list)

            # Rimuovi anche il file in post_pronti
            self._remove_post_file(idea)
            return idea
        return None

    def _update_post_file(self, idea):
        """Update the corresponding file in post_pronti"""
        import glob
        posts_dir = os.path.expanduser('~/SunsetSocial/post_pronti')
        if not os.path.exists(posts_dir):
            return

        # Cerca il file corrispondente per timestamp
        approved_at = idea.get('approved_at', '')
        if approved_at:
            timestamp = approved_at[:19].replace('-', '').replace(':', '').replace('T', '_')
            pattern = os.path.join(posts_dir, f"{timestamp}*")
            files = glob.glob(pattern)
            if files:
                with open(files[0], 'w', encoding='utf-8') as f:
                    json.dump(idea, f, indent=2, ensure_ascii=False)

    def _remove_post_file(self, idea):
        """Remove the corresponding file from post_pronti"""
        import glob
        posts_dir = os.path.expanduser('~/SunsetSocial/post_pronti')
        if not os.path.exists(posts_dir):
            return

        approved_at = idea.get('approved_at', '')
        if approved_at:
            timestamp = approved_at[:19].replace('-', '').replace(':', '').replace('T', '_')
            pattern = os.path.join(posts_dir, f"{timestamp}*")
            files = glob.glob(pattern)
            for f in files:
                os.remove(f)

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
