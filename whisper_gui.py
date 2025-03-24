import os
import threading
import queue
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel
import customtkinter as ctk
import whisper
import subprocess
import ssl
import certifi
import sys

# Fix SSL certificate issues
ssl._create_default_https_context = ssl._create_unverified_context

# Check for FFmpeg and install if necessary
def check_ffmpeg():
    try:
        # Try to run ffmpeg to check if it's installed
        subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return True
    except FileNotFoundError:
        return False

def install_ffmpeg():
    platform = sys.platform
    if platform == 'darwin':  # macOS
        messagebox.showinfo(
            "FFmpeg Required", 
            "FFmpeg is required but not found. Please install it using Homebrew:\n\n" +
            "1. Install Homebrew (if not installed):\n   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"\n\n" +
            "2. Install FFmpeg:\n   brew install ffmpeg\n\n" +
            "After installation, restart this application."
        )
    elif platform == 'win32':  # Windows
        messagebox.showinfo(
            "FFmpeg Required", 
            "FFmpeg is required but not found. Please download and install it:\n\n" +
            "1. Download from: https://ffmpeg.org/download.html\n" +
            "2. Add FFmpeg to your system PATH\n\n" +
            "After installation, restart this application."
        )
    else:  # Linux and others
        messagebox.showinfo(
            "FFmpeg Required", 
            "FFmpeg is required but not found. Please install it using your package manager:\n\n" +
            "For Ubuntu/Debian:\n   sudo apt update && sudo apt install ffmpeg\n\n" +
            "For Fedora:\n   sudo dnf install ffmpeg\n\n" +
            "After installation, restart this application."
        )

# Set appearance mode and default color theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

class WhisperGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Whisper Transcription")
        self.geometry("800x800")
        self.minsize(600, 500)    # Reduced minimum size
        self.configure(fg_color="white")
        
        # Set window icon (if available)
        try:
            self.iconbitmap("icon.ico")
        except:
            pass  # Skip if icon not found
        
        # Configure grid layout
        self.grid_rowconfigure(0, weight=1)  # Make the main content expand
        self.grid_columnconfigure(0, weight=1)
        
        # Variables
        self.file_path = None
        self.model_size = ctk.StringVar(value="base")
        self.result_queue = queue.Queue()
        self.selected_model_button = None
        self.tooltip_window = None
        self.is_transcribing = False
        self.progress_value = ctk.DoubleVar(value=0.0)
        self.progress_text = ctk.StringVar(value="")
        
        # Model information dictionary
        self.model_info = {
            "tiny": {
                "params": "39M parameters",
                "vram": "~1 GB VRAM",
                "speed": "~8x faster than large",
                "recommendation": "💡 Quick tests and low resource devices"
            },
            "base": {
                "params": "74M parameters",
                "vram": "~1 GB VRAM",
                "speed": "~6x faster than large",
                "recommendation": "💡 Good balance for most short clips"
            },
            "small": {
                "params": "244M parameters",
                "vram": "~2 GB VRAM",
                "speed": "~4x faster than large",
                "recommendation": "💡 Recommended for most everyday transcriptions"
            },
            "medium": {
                "params": "769M parameters",
                "vram": "~5 GB VRAM",
                "speed": "~2x faster than large",
                "recommendation": "💡 Better accuracy for challenging audio"
            },
            "large": {
                "params": "1550M parameters",
                "vram": "~10 GB VRAM",
                "speed": "Slowest model",
                "recommendation": "💡 Best accuracy for difficult audio"
            },
            "turbo": {
                "params": "Optimized model",
                "vram": "~4 GB VRAM",
                "speed": "Optimized for real-time",
                "recommendation": "💡 Fast with good accuracy"
            }
        }
        
        # Create UI
        self.create_ui()
        
        # Start queue checker
        self.check_queue()
    
    def create_ui(self):
        # Create main frame with grid layout
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.main_frame)
        self.progress_bar.grid(row=4, column=0, sticky="ew", pady=(10, 10), padx=20)
        self.progress_bar.set(0)
        self.progress_bar.configure(
            mode="determinate",
            progress_color="#25a06e",
            bg_color="transparent",
            fg_color="#E0E0E0",
            height=10,
            corner_radius=2
        )
        
        # Progress text below the grey bar
        self.progress_label = ctk.CTkLabel(
            self.main_frame,
            textvariable=self.progress_text,
            font=ctk.CTkFont(size=14),
            text_color="#666666"
        )
        self.progress_label.grid(row=5, column=0, pady=(5, 10))
        
        # Initially hide progress elements
        self.progress_bar.grid_remove()
        self.progress_label.grid_remove()
        
        # Configure main frame grid
        self.main_frame.grid_rowconfigure(4, weight=1)  # Make transcription section expand
        self.main_frame.grid_columnconfigure(0, weight=1)  # Full width
        
        # Title
        title_label = ctk.CTkLabel(
            self.main_frame, 
            text="Whisper Transcription", 
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#000000"
        )
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Upload frame with white background and green border
        self.upload_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="#ffffff",
            border_color="#25a06e",
            border_width=2,
            corner_radius=10
        )
        self.upload_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20), padx=20)
        self.upload_frame.grid_columnconfigure(0, weight=1)
        
        # Upload icon and text
        upload_icon = ctk.CTkLabel(
            self.upload_frame,
            text="⬆️",
            font=ctk.CTkFont(size=32)
        )
        upload_icon.grid(row=0, column=0, pady=(20, 5))
        
        upload_text = ctk.CTkLabel(
            self.upload_frame,
            text="Click to upload or drag and drop",
            font=ctk.CTkFont(size=16, weight="normal"),
            text_color="#000000"
        )
        upload_text.grid(row=1, column=0)
        
        format_text = ctk.CTkLabel(
            self.upload_frame,
            text="Supported formats: .mp3, .wav, .m4a, .ogg, .flac",
            font=ctk.CTkFont(size=12, weight="normal"),
            text_color="#666666"
        )
        format_text.grid(row=2, column=0, pady=(5, 20))
        
        # Make the entire upload frame clickable
        for widget in [self.upload_frame, upload_icon, upload_text, format_text]:
            widget.bind("<Button-1>", self.select_file)
            widget.configure(cursor="hand2")  # Change cursor to hand on hover
        
        # File selection display
        self.file_label = ctk.CTkLabel(
            self.main_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="#666666"
        )
        self.file_label.grid(row=2, column=0, pady=(0, 20))
        
        # Model selection section
        model_label = ctk.CTkLabel(
            self.main_frame, 
            text="Select Whisper Model",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#000000"
        )
        model_label.grid(row=3, column=0, pady=(0, 10))
        
        # No info button
        
        # Model selection buttons
        model_buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        model_buttons_frame.grid(row=4, column=0, sticky="ew")
        model_buttons_frame.grid_columnconfigure(tuple(range(6)), weight=1)
        
        models = ["tiny", "base", "small", "medium", "large", "turbo"]
        self.model_buttons = {}
        
        for i, model in enumerate(models):
            button = ctk.CTkButton(
                model_buttons_frame,
                text=model,
                width=80,
                height=32,
                corner_radius=8,
                border_width=2,
                fg_color="transparent",
                text_color="#2CC985",
                border_color="#2CC985",
                hover_color="#25a06e",
                font=ctk.CTkFont(size=13),
                command=lambda m=model: self.select_model(m)
            )
            # Make buttons more responsive
            button.configure(cursor="hand2")
            button.grid(row=0, column=i, padx=5)
            self.model_buttons[model] = button
            
            # Create tooltip for model info
            button.bind("<Enter>", lambda e, m=model: self.show_model_tooltip(e, m))
            button.bind("<Leave>", lambda e: self.hide_model_tooltip())
        
        # Set base as default selected model
        self.select_model("base")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.main_frame,
            mode="determinate",
            height=20,
            corner_radius=10
        )
        self.progress_bar.grid(row=5, column=0, sticky="ew", pady=(20, 0), padx=20)
        self.progress_bar.set(0)
        
        # Control buttons frame
        control_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        control_frame.grid(row=6, column=0, pady=(10, 20))
        
        # Clear and Transcribe buttons
        self.clear_button = ctk.CTkButton(
            control_frame,
            text="Clear",
            width=120,
            height=32,
            fg_color="transparent",
            border_width=2,
            border_color="#2CC985",
            text_color="#2CC985",
            hover_color="#25a06e",
            command=self.clear_transcription
        )
        self.clear_button.grid(row=0, column=0, padx=10)
        
        self.transcribe_button = ctk.CTkButton(
            control_frame,
            text="Transcribe",
            width=120,
            height=32,
            fg_color="#2CC985",
            hover_color="#25a06e",
            command=self.start_transcription
        )
        self.transcribe_button.grid(row=0, column=1, padx=10)
        
        # Transcription result
        self.result_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="#ffffff",
            border_color="#2CC985",
            border_width=2,
            corner_radius=10
        )
        self.result_frame.grid(row=7, column=0, sticky="nsew", pady=(0, 20), padx=20)
        self.result_frame.grid_columnconfigure(0, weight=1)
        self.result_frame.grid_rowconfigure(0, weight=1)
        
        self.result_text = ctk.CTkTextbox(
            self.result_frame,
            wrap="word",
            fg_color="transparent",
            border_width=0,
            font=ctk.CTkFont(size=14)
        )
        self.result_text.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
            

    def show_model_tooltip(self, event, model):
        if self.tooltip_window:
            self.hide_model_tooltip()
        
        # Create tooltip window
        self.tooltip_window = Toplevel(self)
        self.tooltip_window.overrideredirect(True)
        self.tooltip_window.configure(bg="#1c1c1c")
        
        # Get model info
        info = self.model_info[model]
        
        # Create tooltip content
        tooltip_frame = ctk.CTkFrame(self.tooltip_window, fg_color="#1c1c1c", corner_radius=8)
        tooltip_frame.pack(padx=2, pady=2)
        
        # Add model info labels
        labels = [
            info["params"],
            info["vram"],
            info["speed"],
            info["recommendation"]
        ]
        
        for i, text in enumerate(labels):
            label = ctk.CTkLabel(
                tooltip_frame,
                text=text,
                font=ctk.CTkFont(size=12),
                text_color="white",
                anchor="w"
            )
            label.pack(padx=10, pady=(5 if i == 0 else 2, 5 if i == len(labels)-1 else 2), anchor="w")
        
        # Position tooltip below the button
        x = event.widget.winfo_rootx()
        y = event.widget.winfo_rooty() + event.widget.winfo_height() + 5
        self.tooltip_window.geometry(f"+{x}+{y}")
    
    def hide_model_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None
    
    def select_file(self, event=None):
        # Provide immediate visual feedback
        self.upload_frame.configure(fg_color="#e0f5ea")
        self.update()
        
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.m4a *.ogg *.flac"),
                ("All Files", "*.*")
            ]
        )
        
        # Reset upload frame color
        self.upload_frame.configure(fg_color="#ffffff")
        
        if file_path:
            self.file_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.configure(
                text=f"Selected: {filename}",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            # Flash effect for successful upload
            self.after(100, lambda: self.file_label.configure(text_color="#2CC985"))
            self.after(1000, lambda: self.file_label.configure(text_color="#666666"))
    
    def clear_transcription(self):
        self.result_text.delete("1.0", "end")
        self.file_label.configure(text="")
        self.file_path = None
        self.progress_bar.set(0)
    
    def start_transcription(self):
        if not self.file_path:
            messagebox.showwarning("No File Selected", "Please select an audio file first.")
            return
        
        if self.is_transcribing:
            messagebox.showwarning("In Progress", "Transcription is already in progress.")
            return
        
        self.is_transcribing = True
        self.transcribe_button.configure(state="disabled")
        self.clear_button.configure(state="disabled")
        self.progress_bar.set(0)
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", "Transcribing...")
        
        # Start transcription in a separate thread
        threading.Thread(target=self.transcribe_audio, daemon=True).start()
    
    def transcribe_audio(self):
        try:
            # Load the model
            model = whisper.load_model(self.model_size.get())
            
            # Transcribe the audio
            result = model.transcribe(self.file_path)
            
            # Put the result in the queue
            self.result_queue.put(("success", result["text"]))
            
        except Exception as e:
            self.result_queue.put(("error", str(e)))
        
        # Update progress
        self.progress_value.set(1.0)
    
    def check_queue(self):
        try:
            status, result = self.result_queue.get_nowait()
            
            if status == "success":
                self.result_text.delete("1.0", "end")
                self.result_text.insert("1.0", result)
            else:
                messagebox.showerror("Error", f"Transcription failed: {result}")
            
            self.is_transcribing = False
            self.transcribe_button.configure(state="normal")
            self.clear_button.configure(state="normal")
            
        except queue.Empty:
            pass
        
        # Update progress bar
        if self.is_transcribing:
            self.progress_bar.set(self.progress_value.get())
        
        # Check queue again after 100ms
        self.after(100, self.check_queue)
        
    def select_model(self, model):
        # Don't do anything if this model is already selected
        if self.selected_model_button == self.model_buttons[model]:
            return
            
        # Update previously selected button
        if self.selected_model_button:
            self.selected_model_button.configure(
                fg_color="transparent",
                text_color="#2CC985",
                border_color="#2CC985",
                font=ctk.CTkFont(size=13, weight="normal")
            )
        
        # Update newly selected button with instant feedback
        self.model_buttons[model].configure(
            fg_color="#2CC985",
            text_color="white",
            border_color="#2CC985",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        
        # Update selected button reference and model size
        self.selected_model_button = self.model_buttons[model]
        self.model_size.set(model)
        
        # Hide tooltip if visible
        self.hide_model_tooltip()

if __name__ == "__main__":
    # Check if FFmpeg is installed before starting the app
    if not check_ffmpeg():
        install_ffmpeg()
    else:
        app = WhisperGUI()
        app.mainloop()
        # We'll add this at the end of the UI creation to ensure it appears at the bottom
    
    def create_transcript_section(self):
        # Create a prominent transcript section with a bold green header
        self.transcript_section = ctk.CTkFrame(self.main_frame, fg_color="#e0f5ea", corner_radius=10, border_width=2, border_color="#2CC985")
        self.transcript_section.grid(row=5, column=0, sticky="nsew", pady=(20, 10))
        
        # Configure transcript section grid
        self.transcript_section.grid_rowconfigure(1, weight=1)  # Make text area expand
        self.transcript_section.grid_columnconfigure(0, weight=1)
        
        # Add a header for the transcript section
        transcript_header = ctk.CTkFrame(self.transcript_section, fg_color="#2CC985", corner_radius=5)
        transcript_header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        transcript_header.grid_columnconfigure(0, weight=1)  # Center the header label
        
        ctk.CTkLabel(
            transcript_header,
            text="✓ TRANSCRIPTION RESULT",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white"
        ).grid(row=0, column=0, pady=5)  # Use grid instead of pack
        
        # Create a frame with border for the transcript
        transcript_frame = ctk.CTkFrame(self.transcript_section, fg_color="white", border_width=1, border_color="#e0e0e0")
        transcript_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        # Configure transcript frame grid
        transcript_frame.grid_rowconfigure(0, weight=1)
        transcript_frame.grid_columnconfigure(0, weight=1)
        
        # Add the transcript text area with improved styling
        self.transcript_area = ctk.CTkTextbox(
            transcript_frame,
            wrap="word",
            font=ctk.CTkFont(size=16),  # Removed bold for better readability
            fg_color="white",
            border_width=0,
            text_color="#333333",
            height=300  # Set a minimum height
        )
        self.transcript_area.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        # Add placeholder text
        self.transcript_area.configure(state="normal")
        self.transcript_area.insert("1.0", "Transcription will appear here after processing...")
        self.transcript_area.configure(state="disabled")
        
        # Set transcript as visible
        self.transcript_visible = True
    
    def create_upload_icon(self):
        # Create a simple upload icon using PIL
        from PIL import Image, ImageDraw
        
        img = Image.new('RGBA', (100, 100), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Draw arrow
        draw.polygon([(50, 20), (70, 40), (60, 40), (60, 70), (40, 70), (40, 40), (30, 40)], fill="#2CC985")
        
        # Draw base line
        draw.rectangle([30, 75, 70, 80], fill="#2CC985")
        
        return img
    
    def on_button_hover(self, event, model, button, is_hover):
        if is_hover and model is not None:
            # Make button text bold on hover for visual feedback
            button.configure(font=ctk.CTkFont(size=13, weight="bold"))
            
            # Add underline effect by changing border color to a brighter shade
            if button.cget("fg_color") == "transparent":
                button.configure(border_color="#1aff9c")
            
            # Show tooltip
            self.show_tooltip(event, model)
        else:
            # Reset text formatting
            button.configure(font=ctk.CTkFont(size=13, weight="normal"))
            
            # Reset border color if not selected
            if button != self.selected_model_button and button.cget("fg_color") == "transparent":
                button.configure(border_color="#2CC985")
            
            # Hide tooltip
            if hasattr(self, 'tooltip_window') and self.tooltip_window:
                self.tooltip_window.destroy()
                self.tooltip_window = None
    
    def show_tooltip(self, event, model):
        # Destroy existing tooltip if any
        if hasattr(self, 'tooltip_window') and self.tooltip_window:
            self.tooltip_window.destroy()
        
        # Create tooltip window
        self.tooltip_window = ctk.CTkToplevel(self)
        self.tooltip_window.overrideredirect(True)  # Remove window decorations
        
        # Create frame with dark green background
        frame = ctk.CTkFrame(self.tooltip_window, fg_color="#0B4F2C", corner_radius=10)
        frame.pack(expand=True, fill="both")
        
        # Model name as title
        title = model.capitalize() + " Model"
        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        ).pack(padx=15, pady=(10, 5))
        
        # Model details
        details = self.model_info[model]
        for key in ['params', 'vram', 'speed']:
            if key in details:
                ctk.CTkLabel(
                    frame,
                    text=f"• {details[key]}",
                    font=ctk.CTkFont(size=13),
                    text_color="white"
                ).pack(padx=15, pady=2, anchor="w")
        
        # Recommendation with lightbulb emoji
        if 'recommendation' in details:
            ctk.CTkLabel(
                frame,
                text=details['recommendation'],
                font=ctk.CTkFont(size=13),
                text_color="white"
            ).pack(padx=15, pady=(2, 10), anchor="w")
        
        # Position tooltip near the button
        x = event.x_root + 20
        y = event.y_root - 10
        self.tooltip_window.geometry(f"+{x}+{y}")
        
        # Bring tooltip to front
        self.tooltip_window.lift()
        self.tooltip_window.attributes('-topmost', True)
        
        # Get model info
        info = self.model_info[model]
        
        # Create content frame
        content_frame = ctk.CTkFrame(info_window, fg_color="transparent")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add header
        ctk.CTkLabel(
            content_frame,
            text=f"{model.capitalize()} Model",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#2CC985"
        ).pack(anchor="w", pady=(0, 15))
        
        # Parameters
        ctk.CTkLabel(
            content_frame,
            text=f"• {info['params']}",
            font=ctk.CTkFont(size=14),
            text_color="#333333"
        ).pack(anchor="w", pady=(0, 10))
        
        # VRAM
        ctk.CTkLabel(
            content_frame,
            text=f"• Requires {info['vram']}",
            font=ctk.CTkFont(size=14),
            text_color="#333333"
        ).pack(anchor="w", pady=(0, 10))
        
        # Speed
        ctk.CTkLabel(
            content_frame,
            text=f"• {info['speed']}",
            font=ctk.CTkFont(size=14),
            text_color="#333333"
        ).pack(anchor="w", pady=(0, 10))
        
        # Recommendation
        ctk.CTkLabel(
            content_frame,
            text=info['recommendation'],
            font=ctk.CTkFont(size=14),
            text_color="#333333"
        ).pack(anchor="w", pady=(0, 10))
        
        # Add close button
        ctk.CTkButton(
            content_frame,
            text="Close",
            command=info_window.destroy,
            fg_color="#2CC985",
            hover_color="#1aff9c",
            width=100
        ).pack(pady=(15, 0))
    
    def select_model(self, model):
        # Reset previous selection
        if self.selected_model_button:
            self.selected_model_button.configure(
                fg_color="transparent",
                text_color="#2CC985",
                border_color="#2CC985",
                border_width=2
            )
        
        # Set new selection
        self.model_buttons[model].configure(
            fg_color="#2CC985",
            text_color="white",
            border_width=0
        )
        self.selected_model_button = self.model_buttons[model]
        self.model_size.set(model)
    
    def show_model_info(self):
        # Show general model info for the ? button
        info_window = ctk.CTkToplevel(self)
        info_window.title("Whisper Model Information")
        info_window.geometry("500x400")
        info_window.resizable(False, False)
        
        # Make the window modal
        info_window.transient(self)
        info_window.grab_set()
        
        # Center the window
        x = self.winfo_x() + (self.winfo_width() // 2) - (500 // 2)
        y = self.winfo_y() + (self.winfo_height() // 2) - (400 // 2)
        info_window.geometry(f"+{x}+{y}")
        
        # Create content frame
        content_frame = ctk.CTkFrame(info_window, fg_color="transparent")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Add header
        ctk.CTkLabel(
            content_frame,
            text="Whisper Model Information",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#2CC985"
        ).pack(anchor="w", pady=(0, 20))
        
        # Add model descriptions
        models = ["tiny", "base", "small", "medium", "large", "turbo"]
        descriptions = [
            "Fastest, lowest accuracy, smallest size (39M parameters)",
            "Fast with decent accuracy (74M parameters)",
            "Good balance of speed and accuracy (244M parameters)",
            "Better accuracy, slower (769M parameters)",
            "Best accuracy, slowest (1550M parameters)",
            "OpenAI's optimized model for real-time transcription"
        ]
        
        for i, (model, desc) in enumerate(zip(models, descriptions)):
            model_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            model_frame.pack(fill=tk.X, pady=(0, 10), anchor="w")
            
            ctk.CTkLabel(
                model_frame,
                text=f"{model.capitalize()}: ",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#333333",
                width=80
            ).pack(side=tk.LEFT)
            
            ctk.CTkLabel(
                model_frame,
                text=desc,
                font=ctk.CTkFont(size=14),
                text_color="#333333"
            ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Add close button
        ctk.CTkButton(
            content_frame,
            text="Close",
            command=info_window.destroy,
            fg_color="#2CC985",
            hover_color="#1aff9c",
            width=100
        ).pack(pady=(15, 0))
    
    def select_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio files", "*.mp3 *.wav *.m4a *.ogg *.flac")]
        )
        if file_path:
            self.file_path = file_path
            filename = os.path.basename(file_path)
            self.file_path_label.configure(text=f"Selected: {filename}")
            # Change upload area appearance to show file is selected
            self.upload_area.configure(border_color="#2CC985")
    
    def clear_all(self):
        # Don't clear if currently transcribing
        if self.is_transcribing:
            messagebox.showwarning("Warning", "Transcription in progress. Please wait for it to complete.")
            return
            
        self.file_path = None
        self.file_path_label.configure(text="")
        self.transcript_area.configure(state="normal")
        self.transcript_area.delete("1.0", tk.END)
        self.transcript_area.configure(state="disabled")
        self.update_status("Ready")
        # Reset upload area appearance
        self.upload_area.configure(border_color="#2CC985")
    
    def transcribe_audio(self, file_path, model_size):
        try:
            # Set environment variable to disable SSL verification
            os.environ['PYTHONHTTPSVERIFY'] = '0'
            
            # Check if FFmpeg is installed (10%)
            self.after(0, lambda: self.progress_bar.set(0.1))
            self.after(0, lambda: self.progress_text.set("10% - Checking FFmpeg..."))
            try:
                subprocess.run(['ffmpeg', '-version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
            except FileNotFoundError:
                error_msg = "Error: FFmpeg is not installed. Please install FFmpeg to use this application."
                print(f"Transcription error: {error_msg}")
                self.result_queue.put(("error", error_msg))
                self.after(0, install_ffmpeg)
                return
            
            # Load the model (30%)
            self.after(0, lambda: self.progress_bar.set(0.3))
            self.after(0, lambda: self.progress_text.set(f"30% - Loading {model_size} model..."))
            print(f"Loading Whisper model: {model_size}")
            model = whisper.load_model(model_size)
            
            # Load audio (50%)
            self.after(0, lambda: self.progress_bar.set(0.5))
            self.after(0, lambda: self.progress_text.set("50% - Loading audio..."))
            print(f"Loading audio file: {file_path}")
            audio = whisper.load_audio(file_path)
            
            # Process audio (70%)
            self.after(0, lambda: self.progress_bar.set(0.7))
            self.after(0, lambda: self.progress_text.set("70% - Processing audio..."))
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            
            # Transcribe (90%)
            self.after(0, lambda: self.progress_bar.set(0.9))
            self.after(0, lambda: self.progress_text.set("90% - Transcribing..."))
            result = model.transcribe(file_path)
            
            # Complete (100%)
            self.after(0, lambda: self.progress_bar.set(1.0))
            self.after(0, lambda: self.progress_text.set("100% - Complete!"))
            print(f"Transcription complete. Length: {len(result['text'])} characters")
            
            # Put result in queue
            self.result_queue.put(("success", result["text"]))
            
        except Exception as e:
            error_msg = str(e)
            if "CUDA" in error_msg:
                error_msg += "\n\nTip: This error may be related to GPU memory. Try using a smaller model or CPU only."
            print(f"Transcription error: {error_msg}")
            self.result_queue.put(("error", error_msg))
    
    def update_status(self, message):
        # This method is called from a thread, so we need to use after
        self.after(0, lambda: self._update_status_ui(message))
    
    def _update_status_ui(self, message):
        # Update the status label and indicator
        self.status_label.configure(text=message)
        
        # Update status indicator and progress bar based on status
        if message == "Ready" or message == "":
            # Gray indicator when idle
            self.status_indicator.configure(fg_color="#cccccc")
            self.is_transcribing = False
            self.progress_bar.stop()
            self.progress_bar.set(0)
            self.transcribe_button.configure(state="normal", text="Transcribe")
        elif message == "Loading model..." or message == "Transcribing..." or message == "Starting...":
            # Green indicator when processing
            self.status_indicator.configure(fg_color="#2CC985")
            self.is_transcribing = True
            self.progress_bar.start()
            self.transcribe_button.configure(state="disabled", text="Transcribing...")
        elif message.startswith("Error"):
            # Red indicator for errors
            self.status_indicator.configure(fg_color="#FF5555")
            self.is_transcribing = False
            self.progress_bar.stop()
            self.progress_bar.set(0)
            self.transcribe_button.configure(state="normal", text="Transcribe")
            self.status_label.configure(text_color="#FF5555")
        elif message == "Transcription complete" or message == "Done.":
            # Blue indicator for completion
            self.status_indicator.configure(fg_color="#55AAFF")
            self.is_transcribing = False
            self.progress_bar.stop()
            self.progress_bar.set(1.0)  # Show as complete
            self.transcribe_button.configure(state="normal", text="Transcribe")
            self.status_label.configure(text_color="#333333")
    
    def start_transcription(self):
        if not self.file_path:
            messagebox.showwarning("Warning", "Please select an audio file.")
            return
        
        # Don't start if already transcribing
        if self.is_transcribing:
            return
        
        self.is_transcribing = True
        model_size = self.model_size.get()
        self.update_status("Starting...")
        
        # Clear previous result and show progress
        self.transcript_text.delete(1.0, tk.END)
        self.progress_bar.grid()
        self.progress_label.grid()
        self.progress_bar.set(0)
        self.progress_text.set("0% - Initializing...")
        
        # Start transcription in a new thread
        thread = threading.Thread(
            target=self.transcribe_audio, 
            args=(self.file_path, model_size)
        )
        thread.daemon = True
        thread.start()
    
    def check_queue(self):
        try:
            msg = self.result_queue.get_nowait()
            
            if isinstance(msg, tuple) and len(msg) == 2:
                status, result = msg
                if status == "success":
                    self.transcript_text.delete(1.0, tk.END)
                    self.transcript_text.insert(tk.END, result)
                    self.update_status("Transcription complete!")
                    # Progress is already at 100%
                else:  # error
                    self.update_status(f"Error: {result}")
                    messagebox.showerror("Error", result)
                    self.progress_frame.grid_remove()
            else:
                # Handle old format messages (shouldn't happen)
                self.transcript_text.delete(1.0, tk.END)
                self.transcript_text.insert(tk.END, msg)
                self.update_status("Transcription complete!")
                self.progress_frame.grid_remove()
            
            self.is_transcribing = False
            
        except queue.Empty:
            pass
        
        # Check again after 100ms
        self.after(100, self.check_queue)

if __name__ == "__main__":
    # Check if FFmpeg is installed before starting the app
    if not check_ffmpeg():
        install_ffmpeg()
    
    app = WhisperGUI()
    app.mainloop()