🎨 Color Palette Generator
An interactive Streamlit web application that uses K-Means Clustering to extract dominant color palettes from any uploaded image. 
Perfect for designers, artists, and developers looking for color inspiration from real-world photography.

🚀 Features
Image Upload: Supports JPG, PNG, and BMP formats.

Dynamic Clustering: Choose the number of colors to extract using a sidebar slider.

Smart Sorting: Sort extracted colors by frequency or luminance.

Color Details: Get Hex codes, RGB values, and saturation levels for every color found.

Visual Feedback: View the original image alongside the generated palette.

🛠️ Technical Stack
Frontend: Streamlit

Image Processing: Pillow (PIL)

Machine Learning: Scikit-Learn (K-Means Clustering)

Data Handling: NumPy

Visualization: Matplotlib

📋 Installation & Setup
Clone the repository:

Bash
git clone https://github.com/your-username/color-palette-generator.git
cd color-palette-generator
Create a virtual environment (optional but recommended):

Bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies:

Bash
pip install -r requirements.txt
Run the app:

Bash
streamlit run app.py
🧠 How it Works
Preprocessing: The uploaded image is converted into a NumPy array and reshaped into a list of RGB pixels.

K-Means Clustering: The algorithm identifies "centroids" in the color space that represent the most dominant groups of colors.

Extraction: Hex codes are calculated from the resulting centroids.

Formatting: Data is displayed using custom Streamlit components and Matplotlib patches.
