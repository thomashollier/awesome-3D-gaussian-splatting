import sys
from src.fix_date import YAMLUpdater
import yaml
import webbrowser
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton,
                           QMessageBox, QTextEdit, QScrollArea, QListWidget,
                           QGridLayout, QDialog)
from PyQt6.QtCore import QTimer
from PyQt6.QtCore import Qt
from pathlib import Path
from typing import Dict, Any

from src.components.widgets import TagButton, URLWidget
from src.components.dialogs import ArxivAddDialog

class YAMLEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.yaml_updater = YAMLUpdater() 
        self.setWindowTitle("3D Gaussian Splatting Paper Editor")
        self.setMinimumSize(1200, 800)
        
        # Initialize member variables
        self.fields = {}
        self.url_widgets = {}
        self.tag_buttons = {}
        self.original_entry_state = None
        self.search_results = []  # Store search result indices
        
        # Available tags
        self.available_tags = [
            "2DGS", "360 degree", "3ster-based", "Acceleration", "Antialiasing", "Autonomous Driving", 
            "Avatar", "Classic Work", "Code", "Compression", "Dataset", "Deblurring", "Densification",
            "Diffusion", "Distributed", "Dynamic", "Editing", "Event Camera", "Feed-Forward", 
            "GAN", "Gaussian Video","Inpainting", "In the Wild", "Language Embedding", "Large-Scale", "Lidar", "LoD",
            "Medicine", "Meshing", "Misc", "Monocular", "Perspective-correct", "Object Detection", 
            "Optimization", "Physics", "Point Cloud", "Poses", "Project", "Ray Tracing", 
            "Rendering", "Relight", "Review", "Robotics", "Segmentation", "SLAM", "Sparse", "Super Resolution",
            "Stereo", "Style Transfer", "Texturing", "Transformer", "Uncertainty", "Video", 
            "Virtual Reality", "World Generation"
        ]
        
        # Load YAML data
        self.load_yaml()
        self.current_index = 0
        
        # Setup UI
        self.setup_ui()
        self.setup_status_bar()
        self.show_current_entry()

    def safe_sort_key(self, x: Dict[str, Any]) -> tuple:
            """Safe sort key that handles None values and missing fields."""
            # Get publication date, default to '9999' for sorting
            pub_date = x.get('publication_date', '9999')
            if not isinstance(pub_date, str):
                pub_date = '9999'
                
            # Get last name of first author, default to 'z' for sorting
            authors = x.get('authors', '')
            if authors and isinstance(authors, str):
                try:
                    first_author = authors.split(',')[0].strip()
                    last_name = first_author.split()[-1].lower() if first_author else 'z'
                except Exception:
                    last_name = 'z'
            else:
                last_name = 'z'
                
            # Get title, default to 'z' for sorting
            title = x.get('title', '')
            if not isinstance(title, str):
                title = 'z'
            else:
                title = title.lower()
                
            # Get date source for priority
            date_source = x.get('date_source', 'unknown')
            source_priority = {'arxiv': 0, 'estimated': 1, 'unknown': 2}
            
            return (pub_date, source_priority.get(date_source, 2), last_name, title)

    def load_yaml(self):
        """Load and sort YAML data with safe handling of missing or invalid values."""
        try:
            print("Loading YAML file")  # Debug print
            with open("awesome_3dgs_papers.yaml", 'r', encoding='utf-8') as file:
                self.data = yaml.safe_load(file)
            
            if not isinstance(self.data, list):
                raise ValueError("YAML file does not contain a list of papers")

            # Sort data using the safe sort key
            self.data.sort(key=self.safe_sort_key, reverse=True)  # Newest first
            print(f"Loaded {len(self.data)} entries")  # Debug print
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load YAML file: {str(e)}")
            sys.exit(1)

    def setup_status_bar(self):
        self.statusBar().showMessage("")
        self.save_indicator = QLabel("")
        self.statusBar().addPermanentWidget(self.save_indicator)

    def show_save_feedback(self, success=True):
        if success:
            self.save_indicator.setText("✓ Changes saved")
            self.save_indicator.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.save_indicator.setText("⚠ Save failed")
            self.save_indicator.setStyleSheet("color: #f44336; font-weight: bold;")
        QTimer.singleShot(1500, self.clear_save_indicator)

    def clear_save_indicator(self):
        self.save_indicator.setText("")
        self.save_indicator.setStyleSheet("")

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Navigation with page input and search
        nav_layout = QHBoxLayout()
        nav_buttons_layout = QHBoxLayout()
        self.nav_layout = nav_layout
        self.add_arxiv_button()
        self.prev_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.delete_button = QPushButton("Delete Entry")
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        self.delete_button.clicked.connect(self.delete_current_entry)
        
        nav_buttons_layout.addWidget(self.prev_button)
        nav_buttons_layout.addWidget(self.next_button)
        nav_buttons_layout.addWidget(self.delete_button)
        self.entry_counter = QLabel()
        
        # Page navigation
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("Go to:"))
        self.page_input = QLineEdit()
        self.page_input.setMaximumWidth(50)
        self.page_input.returnPressed.connect(self.go_to_page)
        page_layout.addWidget(self.page_input)
        
        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by title or authors...")
        self.search_input.returnPressed.connect(self.search_entry)
        search_layout.addWidget(self.search_input)
        
        nav_layout.addLayout(nav_buttons_layout)
        nav_layout.addLayout(page_layout)
        nav_layout.addWidget(self.entry_counter)
        nav_layout.addLayout(search_layout)
        main_layout.addLayout(nav_layout)
        
        # Connect navigation buttons
        self.prev_button.clicked.connect(self.prev_entry)
        self.next_button.clicked.connect(self.next_entry)
        
        # Main content area
        content_layout = QHBoxLayout()
        
        # Form layout (left side)
        form_widget = QWidget()
        self.form_layout = QVBoxLayout(form_widget)
        
        # Basic fields
        basic_fields = ['id', 'title', 'authors', 'year', 'publication_date']  # Removed date_source
        for field in basic_fields:
            field_layout = QHBoxLayout()
            label = QLabel(field.replace('_', ' ').title() + ":")
            label.setMinimumWidth(100)
            
            # Create normal field - let Qt handle the styling consistently
            self.fields[field] = QLineEdit()
            if field == 'publication_date':
                self.fields[field].setReadOnly(True)
            else:
                self.fields[field].textChanged.connect(self.auto_save)
                
            field_layout.addWidget(label)
            field_layout.addWidget(self.fields[field])
            self.form_layout.addLayout(field_layout)

        # URL fields with open buttons
        url_fields = ['project_page', 'paper', 'code', 'video']
        for field in url_fields:
            widget = URLWidget(field.replace('_', ' ').title() + ":")
            widget.open_button.clicked.connect(lambda checked, f=field: self.open_url(f))
            widget.url_input.textChanged.connect(self.handle_url_change)
            self.url_widgets[field] = widget
            self.form_layout.addWidget(widget)
        
        # Abstract field
        abstract_layout = QVBoxLayout()
        abstract_label = QLabel("Abstract:")
        self.fields['abstract'] = QTextEdit()
        self.fields['abstract'].textChanged.connect(self.auto_save)
        abstract_layout.addWidget(abstract_label)
        abstract_layout.addWidget(self.fields['abstract'])
        self.form_layout.addLayout(abstract_layout)
        
        # Current tags list
        current_tags_layout = QVBoxLayout()
        current_tags_label = QLabel("Current Tags:")
        self.current_tags_list = QListWidget()
        current_tags_layout.addWidget(current_tags_label)
        current_tags_layout.addWidget(self.current_tags_list)
        self.form_layout.addLayout(current_tags_layout)
        
        # Wrap form in scroll area
        form_scroll = QScrollArea()
        form_scroll.setWidget(form_widget)
        form_scroll.setWidgetResizable(True)
        content_layout.addWidget(form_scroll)
        
        # Tags grid (right side)
        tags_widget = QWidget()
        tags_layout = QGridLayout(tags_widget)
        tags_layout.setSpacing(5)
        
        # Create tag buttons in a grid
        cols = 4  # Number of columns in the grid
        for i, tag in enumerate(self.available_tags):
            btn = TagButton(tag)
            btn.clicked.connect(self.update_tags)
            self.tag_buttons[tag] = btn
            row = i // cols
            col = i % cols
            tags_layout.addWidget(btn, row, col)
        
        content_layout.addWidget(tags_widget)
        main_layout.addLayout(content_layout)

    def auto_save(self):
        """Automatically save changes with date updating"""
        entry = self.data[self.current_index]
        
        # Update basic fields
        for field, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                value = widget.text()
            elif isinstance(widget, QTextEdit):
                value = widget.toPlainText()
            
            if value.strip() == '':
                value = None
            entry[field] = value
        
        # Update URL fields
        for field, widget in self.url_widgets.items():
            value = widget.url_input.text()
            if value.strip() == '':
                value = None
            entry[field] = value
        
        # Update tags
        entry['tags'] = sorted([tag for tag, btn in self.tag_buttons.items() if btn.isChecked()])
        
        # Process date information if needed
        if 'publication_date' not in entry:
            updated_entry, success = self.yaml_updater.process_paper(entry)
            if success:
                entry.update(updated_entry)
        
        try:
            # Sort data before saving
            self.data.sort(key=self.yaml_updater.safe_sort_key, reverse=True)
            
            # Find the new index of the current entry after sorting
            current_entry_id = entry['id']
            self.current_index = next(i for i, e in enumerate(self.data) if e['id'] == current_entry_id)
            
            with open("awesome_3dgs_papers.yaml", 'w', encoding='utf-8') as file:
                yaml.dump(self.data, file, sort_keys=False, allow_unicode=True)
            
            self.show_save_feedback(True)
            self.original_entry_state = self.get_entry_state(entry)
            self.entry_counter.setText(f"Entry {self.current_index + 1} of {len(self.data)}")
            return True
        except Exception as e:
            self.show_save_feedback(False)
            return False

    def handle_url_change(self):
        self.update_automatic_tags()
        self.auto_save()

    def get_entry_state(self, entry):
        return {
            'basic_fields': {field: entry.get(field, '') for field in self.fields.keys()},
            'url_fields': {field: entry.get(field, '') for field in self.url_widgets.keys()},
            'tags': set(entry.get('tags', []))
        }

    def update_tags(self):
        current_tags = [tag for tag, btn in self.tag_buttons.items() if btn.isChecked()]
        self.current_tags_list.clear()
        self.current_tags_list.addItems(sorted(current_tags))
        self.auto_save()

    def update_automatic_tags(self):
        current_tags = set(tag for tag, btn in self.tag_buttons.items() if btn.isChecked())
        
        auto_tag_mapping = {
            'Project': 'project_page',
            'Code': 'code',
            'Video': 'video'
        }
        
        for tag, field in auto_tag_mapping.items():
            if self.url_widgets[field].url_input.text().strip():
                current_tags.add(tag)
            else:
                current_tags.discard(tag)
        
        for tag, btn in self.tag_buttons.items():
            btn.setChecked(tag in current_tags)
        
        self.current_tags_list.clear()
        self.current_tags_list.addItems(sorted(current_tags))

    def clear_search_results(self):
        self.search_results = []
        self.statusBar().clearMessage()
        self.search_input.clear()

    def show_current_entry(self):
        entry = self.data[self.current_index]
        
        self.original_entry_state = self.get_entry_state(entry)
        self.entry_counter.setText(f"Entry {self.current_index + 1} of {len(self.data)}")
        
        for field, widget in self.fields.items():
            value = entry.get(field, '')
            if isinstance(widget, QLineEdit):
                widget.blockSignals(True)
                widget.setText(str(value) if value is not None else '')
                widget.blockSignals(False)
            elif isinstance(widget, QTextEdit):
                widget.blockSignals(True)
                widget.setText(str(value) if value is not None else '')
                widget.blockSignals(False)
        
        for field, widget in self.url_widgets.items():
            value = entry.get(field, '')
            widget.url_input.blockSignals(True)
            widget.url_input.setText(str(value) if value is not None else '')
            widget.url_input.blockSignals(False)
        
        current_tags = set(entry.get('tags', []))
        for tag, btn in self.tag_buttons.items():
            btn.blockSignals(True)
            btn.setChecked(tag in current_tags)
            btn.blockSignals(False)
        
        self.current_tags_list.clear()
        self.current_tags_list.addItems(sorted(current_tags))

    def search_entry(self):
        search_term = self.search_input.text().lower()
        if not search_term:
            return

        self.search_results = []
        for i, entry in enumerate(self.data):
            title = entry.get('title', '') or ''
            authors = entry.get('authors', '') or ''
            tags = entry.get('tags', [])
            
            title_match = search_term in title.lower()
            authors_match = search_term in authors.lower()
            tags_match = any(search_term in (tag or '').lower() for tag in tags)
            
            if title_match or authors_match or tags_match:
                self.search_results.append(i)
        
        if not self.search_results:
            QMessageBox.information(self, "Search Results", "No matches found.")
            return
            
        if self.current_index in self.search_results:
            current_pos = self.search_results.index(self.current_index)
            next_pos = (current_pos + 1) % len(self.search_results)
            self.current_index = self.search_results[next_pos]
        else:
            self.current_index = self.search_results[0]
            
        self.show_current_entry()
        current_result = self.search_results.index(self.current_index) + 1
        self.statusBar().showMessage(
            f"Showing result {current_result} of {len(self.search_results)}. "
            "Press Enter to see next result."
        )

    def open_url(self, field):
        url = self.url_widgets[field].url_input.text()
        if url:
            webbrowser.open(url)

    def go_to_page(self):
        try:
            page = int(self.page_input.text())
            if 1 <= page <= len(self.data):
                self.current_index = page - 1
                self.clear_search_results()
                self.show_current_entry()
            self.page_input.clear()
        except ValueError:
            pass

    def prev_entry(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.clear_search_results()
            self.show_current_entry()

    def next_entry(self):
        if self.current_index < len(self.data) - 1:
            self.current_index += 1
            self.clear_search_results()
            self.show_current_entry()

    def delete_current_entry(self):
        entry = self.data[self.current_index]
        title = entry.get('title', 'this entry')
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText(f"Are you sure you want to delete '{title}'?")
        msg.setWindowTitle("Confirm Deletion")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                # Delete thumbnail if it exists
                thumbnail_path = Path(f"assets/thumbnails/{entry['id']}.jpg")
                if thumbnail_path.exists():
                    thumbnail_path.unlink()
                
                # Delete the entry
                del self.data[self.current_index]
                
                # Save the changes
                with open("awesome_3dgs_papers.yaml", 'w', encoding='utf-8') as file:
                    yaml.dump(self.data, file, sort_keys=False, allow_unicode=True)
                self.show_save_feedback(True)
                
                if self.current_index >= len(self.data):
                    self.current_index = len(self.data) - 1
                
                if self.data:
                    self.show_current_entry()
                else:
                    self.close()
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save changes: {str(e)}")
                
    def add_arxiv_button(self):
        self.arxiv_button = QPushButton("Add from arXiv")
        self.arxiv_button.clicked.connect(self.show_arxiv_dialog)
        self.nav_layout.addWidget(self.arxiv_button)

    def refresh_ui(self):
        """Force a complete UI refresh with correct positioning"""
        print("Starting refresh_ui")
        old_index = self.current_index
        old_id = self.data[old_index]['id'] if self.data else None
        
        self.load_yaml()
        
        # Find the index of the entry with the same ID
        if old_id:
            try:
                self.current_index = next(i for i, entry in enumerate(self.data) if entry['id'] == old_id)
            except StopIteration:
                self.current_index = 0
        
        self.show_current_entry()
        self.clear_search_results()
        self.entry_counter.setText(f"Entry {self.current_index + 1} of {len(self.data)}")
        QApplication.processEvents()
        print(f"Finished refresh_ui at index {self.current_index}")

    def show_arxiv_dialog(self):
        print("Opening arXiv dialog")
        dialog = ArxivAddDialog(self)
        result = dialog.exec()
        print(f"Dialog result: {result}")
        if result == 1:
            print("Dialog accepted, getting newly added entry")
            
            # Read the current YAML file
            with open("awesome_3dgs_papers.yaml", 'r', encoding='utf-8') as file:
                current_data = yaml.safe_load(file)
            
            # Get the newest entry and its ID before any modifications
            new_entry = current_data[-1]
            new_entry_id = new_entry['id']
            print(f"New entry ID: {new_entry_id}")
            
            # Update date information
            updated_entry, success = self.yaml_updater.process_paper(new_entry)
            if success:
                current_data[-1] = updated_entry
                
                # Sort the data
                current_data.sort(key=self.yaml_updater.safe_sort_key, reverse=True)
                
                # Save the updated and sorted data
                with open("awesome_3dgs_papers.yaml", 'w', encoding='utf-8') as file:
                    yaml.dump(current_data, file, sort_keys=False, allow_unicode=True)
            
            # Reload the data
            self.load_yaml()
            
            # Find the index of the new entry in the sorted data
            try:
                self.current_index = next(i for i, e in enumerate(self.data) if e['id'] == new_entry_id)
                print(f"Found new entry at index {self.current_index}")
            except StopIteration:
                print(f"Warning: Could not find entry with ID {new_entry_id}")
                self.current_index = 0
            
            # Show the entry
            self.show_current_entry()
            self.clear_search_results()
            self.entry_counter.setText(f"Entry {self.current_index + 1} of {len(self.data)}")
            print(f"Now showing entry {self.current_index + 1} of {len(self.data)}")

def main():
    app = QApplication(sys.argv)
    editor = YAMLEditor()
    editor.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()