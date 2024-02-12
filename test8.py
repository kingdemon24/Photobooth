import tkinter as tk
from tkinter import filedialog, messagebox
import cv2
import os
import requests
from PIL import Image, ImageTk
from io import BytesIO

images_folder = r"E:\Photobooth\nature"
output_folder_with_bg = r"E:\Photobooth\output\bg"
output_folder_with_no_bg = r"E:\Photobooth\output\no_bg"

class WebcamApp:
    def __init__(self, window, window_title):
        self.window = window
        self.window.title(window_title)
        
        # OpenCV setup
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Create canvas for displaying images
        self.canvas = tk.Canvas(window, width=640, height=480)
        self.canvas.pack()

        # Frame for background image selection buttons
        self.background_selection_frame = tk.Frame(window)
        self.background_selection_frame.pack()

        # Button to capture image
        self.capture_button = tk.Button(window, text="Capture", command=self.capture_and_remove_bg, state="disabled")
        self.capture_button.pack()

        # Variable to store selected background image
        self.selected_bg_path = None

        # Display available background images for selection
        self.display_background_images()

        # OpenCV loop
        self.update()
        
        window.mainloop()

    def display_background_images(self):
        if not os.path.exists(images_folder):
            print("Background images folder not found.")
            return

        # Get list of available background images
        images = os.listdir(images_folder)
        for image_name in images:
            image_path = os.path.join(images_folder, image_name)
            image = cv2.imread(image_path)
            image = cv2.resize(image, (100, 100))  # Resize for display
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert to RGB format
            photo = ImageTk.PhotoImage(image=Image.fromarray(image))
            button = tk.Button(self.background_selection_frame, image=photo)
            button.image = photo
            button.image_path = image_path  # Set custom attribute
            button.pack(side=tk.LEFT, padx=10)
            
            # Bind double-click event to select background image
            button.bind("<Double-Button-1>", lambda event, img=image_path: self.select_background(img))

    def select_background(self, image_path):
        # Update selected background image
        self.selected_bg_path = image_path

        # Indicate selection visually (optional)
        for widget in self.background_selection_frame.winfo_children():
            if widget.image_path == self.selected_bg_path:
                widget.config(relief=tk.SOLID, borderwidth=3)
            else:
                widget.config(relief=tk.FLAT)

        # Enable capture button
        self.capture_button["state"] = "normal"


    def show_preview(self):
    # Read the selected background image
        if not self.selected_bg_path:
            messagebox.showerror("Error", "No background image selected.")
            return

        bg = cv2.imread(self.selected_bg_path)
        if bg is None:
            messagebox.showerror("Error", "Failed to load background image.")
            return

        bg = cv2.resize(bg, (640, 480))  # Resize background to match canvas size

        # Increase brightness of the background image by 50%
        bg = cv2.convertScaleAbs(bg, alpha=1.5, beta=0)

        # Load the captured image from file (output.png)
        captured_image_path = "output.png"
        captured_image = cv2.imread(captured_image_path)
        if captured_image is None:
            messagebox.showerror("Error", f"Failed to load {captured_image_path}.")
            return

        # Increase brightness of the captured image by 50%
        captured_image = cv2.convertScaleAbs(captured_image, alpha=1.5, beta=0)

        # Resize the captured image to fit within the background
        captured_image_resized = cv2.resize(captured_image, (bg.shape[1], bg.shape[0]))

        # Add an alpha channel to the captured image
        captured_image_with_alpha = cv2.cvtColor(captured_image_resized, cv2.COLOR_BGR2BGRA)

        # Calculate the position to center the captured image on the background
        x_offset = (bg.shape[1] - captured_image_resized.shape[1]) // 2
        y_offset = (bg.shape[0] - captured_image_resized.shape[0]) // 2

        # Overlay the captured image on top of the background with reduced transparency
        overlay_alpha = 0.8  # Adjust this value to change the transparency level
        bg[y_offset:y_offset+captured_image_resized.shape[0], x_offset:x_offset+captured_image_resized.shape[1]] = cv2.addWeighted(
            captured_image_with_alpha, overlay_alpha, bg[y_offset:y_offset+captured_image_resized.shape[0], x_offset:x_offset+captured_image_resized.shape[1]], 1 - overlay_alpha, 0)

        # Convert the composite image to ImageTk format
        result = Image.fromarray(bg)
        result = ImageTk.PhotoImage(result)

        # Create preview dialog
        self.preview_dialog = tk.Toplevel(self.window)
        self.preview_dialog.title("Preview")
        preview_canvas = tk.Canvas(self.preview_dialog, width=640, height=480)
        preview_canvas.pack()

        # Display the composite image on the canvas
        preview_canvas.create_image(0, 0, anchor=tk.NW, image=result)
        preview_canvas.result = result

        # Buttons for save and retake
        save_button = tk.Button(self.preview_dialog, text="Save", command=lambda: self.save_image(bg))
        save_button.pack(side=tk.LEFT, padx=10)
        retake_button = tk.Button(self.preview_dialog, text="Retake", command=self.retake_image)
        retake_button.pack(side=tk.LEFT, padx=10)


    def capture_and_remove_bg(self):
        ret, frame = self.cap.read()
        if ret:
            # Show preview if frame is captured successfully
            self.remove_background_and_show_preview(frame)
        else:
            print("Error: Failed to capture frame.")

    def remove_background_and_show_preview(self, frame):
        if frame is None:
            print("Error: Invalid frame.")
            return

        _, buffer = cv2.imencode('.jpg', frame)
        image_bytes = buffer.tobytes()

        # Remove background
        bg_removed_image = self.remove_background_with_removebg(image_bytes, "output.png")

        if bg_removed_image is not None:
            # Show preview
            self.show_preview()


    def remove_background_with_removebg(self, image, output_path):
        api_key = "X8thSaKwpoom8pK1KSPsMZsR"  # Your remove.bg API key

        # Initialize remove.bg API client
        url = "https://api.remove.bg/v1.0/removebg"
        headers = {'X-Api-Key': api_key}
        files = {'image_file': image}
        data = {'size': 'auto'}

        # Send request to remove background
        response = requests.post(url, headers=headers, files=files, data=data)

        # Check if request was successful
        if response.status_code == 200:
            # Convert image bytes to PIL Image
            img = Image.open(BytesIO(response.content))
            # Save output image
            img.save(output_path)
            return img
        else:
            print(f"Error: {response.status_code}, {response.text}")
            return None

    def save_image(self, img):
        # Save the captured image
        img.save("captured_image.png")
        messagebox.showinfo("Saved", "Captured image saved successfully.")
        self.preview_dialog.destroy()

    def retake_image(self):
        # Close the preview dialog and allow capturing another image
        self.preview_dialog.destroy()
        self.capture_button["state"] = "normal"

    def update(self):
        # Get a frame from the video source
        ret, frame = self.cap.read()

        if ret:
            # Convert the frame to RGBA format
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

            # Convert the frame to ImageTk format
            img = Image.fromarray(frame)
            img = ImageTk.PhotoImage(image=img)

            # Update the displayed image
            self.canvas.create_image(0, 0, anchor=tk.NW, image=img)
            self.canvas.img = img

        # Call the update function after 15 milliseconds
        self.window.after(15, self.update)

# Create a window and pass it to the WebcamApp class
root = tk.Tk()
app = WebcamApp(root, "Photobooth with Background")
