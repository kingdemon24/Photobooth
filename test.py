import cv2
import numpy as np
import os
import random
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk, ImageDraw
import datetime

# Global variables to store selected background image and captured image
selected_background = None
captured_image = None

# Path to the folder containing images of natural scenarios and landscapes
images_folder = r"E:\Photobooth\nature"
output_folder = r"E:\Photobooth\output"

def show_preview_dialog(image):
    dialog = tk.Toplevel()
    dialog.title("Preview")
    photo = ImageTk.PhotoImage(image=Image.fromarray(image))
    label = tk.Label(dialog, image=photo)
    label.image = photo
    label.pack()
    # Add Save button to save the image
    save_button = tk.Button(dialog, text="Save", command=lambda: save_image_with_background(image))
    save_button.pack(side=tk.LEFT)
    # Add Retake button to capture photo again
    retake_button = tk.Button(dialog, text="Retake", command=dialog.destroy)
    retake_button.pack(side=tk.RIGHT)
    
# Function to capture an image using the camera
def capture_image(cap):
    global captured_image
    ret, frame = cap.read()
    captured_image = frame.copy()

# Function to remove background from the captured image using background subtraction
def remove_background(image):
    # Convert image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Create background subtractor
    background_subtractor = cv2.createBackgroundSubtractorMOG2()
    # Apply background subtraction
    fg_mask = background_subtractor.apply(gray)
    # Apply morphological operations to enhance mask
    kernel = np.ones((5,5),np.uint8)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
    fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
    # Invert mask
    fg_mask = cv2.bitwise_not(fg_mask)
    # Apply mask to image
    result = cv2.bitwise_and(image, image, mask=fg_mask)
    return result

# Function to capture and display the image with the selected background
def capture_and_display_image(cap, label):
    global captured_image
    capture_image(cap)
    if captured_image is not None:
        # Remove background from the captured image
        captured_image_no_bg = remove_background(captured_image)
        # Overlay captured image with transparent background on the selected background
        opacity = 0.5  # Adjust opacity level as needed (0 to 1)
        transparent_captured_image = apply_transparent_background(captured_image_no_bg, 0)  # Apply transparent background
        captured_image_with_background = overlay_images(selected_background, transparent_captured_image, 0, 0)
        if captured_image_with_background is not None:
            captured_image_with_background = cv2.cvtColor(captured_image_with_background, cv2.COLOR_BGR2RGB)
            photo = ImageTk.PhotoImage(image=Image.fromarray(captured_image_with_background))
            label.config(image=photo)
            label.image = photo
            # Show preview dialog with captured image without background
            show_preview_dialog(cv2.cvtColor(captured_image_no_bg, cv2.COLOR_BGR2RGB))


# Function to capture and display the image with the selected background
def capture_and_display_image(cap, label):
    global captured_image
    capture_image(cap)
    if captured_image is not None:
        # Remove background from the captured image
        captured_image_no_bg = remove_background(captured_image)
        # Overlay captured image with transparent background on the selected background
        opacity = 0.5  # Adjust opacity level as needed (0 to 1)
        transparent_captured_image = apply_transparent_background(captured_image_no_bg, 0)  # Apply transparent background
        captured_image_with_background = overlay_images(selected_background, transparent_captured_image, 0, 0)
        if captured_image_with_background is not None:
            captured_image_with_background = cv2.cvtColor(captured_image_with_background, cv2.COLOR_BGR2RGB)
            photo = ImageTk.PhotoImage(image=Image.fromarray(captured_image_with_background))
            label.config(image=photo)
            label.image = photo

# Function to apply transparent color background to the captured image
def apply_transparent_background(image, transparency):
    b_channel, g_channel, r_channel = cv2.split(image)
    alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * transparency
    return cv2.merge((b_channel, g_channel, r_channel, alpha_channel))

# Function to overlay the captured image with transparent background on the background image
def overlay_images(background, overlay, x, y):
    h, w = overlay.shape[:2]
    overlay_image = background.copy()
    overlay = cv2.resize(overlay, (w, h))  # Resize overlay to match dimensions
    overlay = overlay[:,:,:3]  # Keep only RGB channels, discard alpha channel
    overlay_image[y:y+h, x:x+w] = overlay
    return overlay_image

# Function to save the captured image with background
def save_image_with_background(image):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = os.path.join(output_folder, f"captured_image_{current_time}.jpg")
    cv2.imwrite(output_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    print(f"Image saved at: {output_path}")

# Main function to run the photobooth
def run_photobooth():
    global selected_background, captured_image
    
    root = tk.Tk()
    root.title("Photobooth")
    
    # Open the camera
    cap = cv2.VideoCapture(0)
    
    # Frame to display background selection
    background_selection_frame = tk.Frame(root)
    background_selection_frame.pack(side=tk.BOTTOM, pady=10)
    
    # Frame to display capture button
    capture_frame = tk.Frame(root)
    
    # Variable to keep track of the selected background button
    selected_button = None
    # Function to create a checkmark icon
    def create_checkmark_icon(width, height):
        image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        draw.polygon([(width * 0.8, height * 0.2), (width, 0), (width, height * 0.3), (width * 0.85, height * 0.45), (width * 0.45, height * 0.9), (0, height * 0.4), (0, height * 0.2), (width * 0.8, height * 0.2)], fill=(0, 255, 0), outline=(0, 255, 0))
        return ImageTk.PhotoImage(image)
    # Function to update selected background
    def update_selected_background(image_path, button):
        nonlocal selected_button
        global selected_background
        selected_background = cv2.imread(image_path)
        capture_and_display_image(cap, label)
        
        # Reset border and checkmark on previously selected button
        if selected_button:
            selected_button.config(relief=tk.RAISED)
            selected_button.checkmark_label.config(image=None)
        
        # Set border and checkmark on selected button
        button.config(relief=tk.SOLID, borderwidth=3)
        checkmark_icon = create_checkmark_icon(20, 20)
        button.checkmark_label = tk.Label(button, image=checkmark_icon, bg="white")
        button.checkmark_label.image = checkmark_icon
        button.checkmark_label.place(relx=1.0, rely=0.0, anchor=tk.NE)
        selected_button = button
        
        # Show capture button
        capture_frame.pack(side=tk.TOP, pady=10)
    
    # Function to handle double-click event on background buttons
    def on_background_double_click(image_path, button):
        update_selected_background(image_path, button)
    
    # Display available background images for selection
    images = os.listdir(images_folder)
    for image_name in images:
        image_path = os.path.join(images_folder, image_name)
        image = cv2.imread(image_path)
        image = cv2.resize(image, (100, 100))  # Resize for display
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Convert to RGB format
        photo = ImageTk.PhotoImage(image=Image.fromarray(image))
        button = tk.Button(background_selection_frame, image=photo)
        button.image = photo
        button.pack(side=tk.LEFT, padx=10)
        
        # Bind double-click event with a lambda function
        button.bind("<Double-Button-1>", lambda event, i=image_path, b=button: on_background_double_click(i, b))
    
    # Function to capture and save the image with background
    def capture_and_save_image():
        if captured_image is not None:
            captured_image_with_background = overlay_images(selected_background, captured_image, 0, 0)
            if captured_image_with_background is not None:
                save_image_with_background(cv2.cvtColor(captured_image_with_background, cv2.COLOR_BGR2RGB))
                show_preview_dialog(cv2.cvtColor(captured_image_with_background, cv2.COLOR_BGR2RGB))
    
    # Capture button
    capture_button = tk.Button(capture_frame, text="Capture", command=capture_and_save_image)
    capture_button.pack()
    
    # Function to show a preview dialog for the captured image
    def show_preview_dialog(image):
        dialog = tk.Toplevel(root)
        dialog.title("Preview")
        photo = ImageTk.PhotoImage(image=Image.fromarray(image))
        label = tk.Label(dialog, image=photo)
        label.image = photo
        label.pack()
        # Add Save button to save the image
        save_button = tk.Button(dialog, text="Save", command=lambda: save_image_with_background(image))
        save_button.pack(side=tk.LEFT)
        # Add Retake button to capture photo again
        retake_button = tk.Button(dialog, text="Retake", command=lambda: dialog.destroy())
        retake_button.pack(side=tk.RIGHT)
    
    # Function to update the camera frame
    def update_frame():
        ret, frame = cap.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert to RGB format
        photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
        label.config(image=photo)
        label.image = photo
        label.after(10, update_frame)  # Update every 10 milliseconds
    
    # Label to display the camera frame
    label = tk.Label(root)
    label.pack()
    
    # Start updating the camera frame
    update_frame()
    
    root.mainloop()

    # Release the camera
    cap.release()

if __name__ == "__main__":
    run_photobooth()
