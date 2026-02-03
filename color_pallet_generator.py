import streamlit as st
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import Counter
import colorsys
import io

def rgb_to_hex(rgb):
    """Convert RGB tuple to HEX string"""
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def hex_to_rgb(hex_color):
    """Convert HEX string to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_dominant_colors(image, num_colors=5):
    """Extract dominant colors from image using K-means clustering"""
    # Convert image to RGB if it's not already
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Resize image to reduce computation time
    image = image.resize((150, 150))
    
    # Convert to numpy array and reshape
    img_array = np.array(image)
    img_array = img_array.reshape((img_array.shape[0] * img_array.shape[1], 3))
    
    # Apply K-means clustering
    kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10)
    kmeans.fit(img_array)
    
    # Get the dominant colors
    colors = kmeans.cluster_centers_
    
    # Convert to integers
    colors = colors.astype(int)
    
    # Sort by frequency
    labels = kmeans.labels_
    label_counts = Counter(labels)
    sorted_colors = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Get colors in order of frequency
    dominant_colors = []
    for label, count in sorted_colors:
        dominant_colors.append(colors[label])
    
    return dominant_colors

def get_color_info(rgb_color):
    """Get detailed color information"""
    r, g, b = rgb_color
    h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
    
    # Convert HSL values to appropriate ranges
    hue = int(h * 360)
    saturation = int(s * 100)
    lightness = int(l * 100)
    
    # Determine color family
    if lightness < 20:
        color_family = "Dark"
    elif lightness > 80:
        color_family = "Light"
    else:
        color_family = "Medium"
    
    # Determine primary component
    if r >= g and r >= b:
        primary_component = "Red"
    elif g >= r and g >= b:
        primary_component = "Green"
    else:
        primary_component = "Blue"
    
    return {
        "HEX": rgb_to_hex(rgb_color),
        "RGB": f"rgb({r}, {g}, {b})",
        "HSL": f"hsl({hue}, {saturation}%, {lightness}%)",
        "Primary Component": primary_component,
        "Brightness Level": color_family,
        "Saturation %": saturation
    }

def create_palette_visualization(colors, hex_colors):
    """Create a visual representation of the color palette"""
    fig, ax = plt.subplots(figsize=(12, 2))
    
    for i, hex_color in enumerate(hex_colors):
        rect = patches.Rectangle((i, 0), 1, 1, linewidth=1, 
                                edgecolor='black', facecolor=hex_color)
        ax.add_patch(rect)
        ax.text(i + 0.5, 0.5, hex_color, ha='center', va='center', 
                fontsize=12, fontweight='bold', color='white' if 
                int(hex_color[1:3], 16) + int(hex_color[3:5], 16) + 
                int(hex_color[5:7], 16) < 384 else 'black')
    
    ax.set_xlim(0, len(hex_colors))
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_aspect('equal')
    
    return fig

def main():
    st.set_page_config(
        page_title="Color Palette Generator",
        page_icon="🎨",
        layout="wide"
    )

    st.title("🎨 Color Palette Generator")
    st.subheader("Upload an image to extract its dominant colors and create beautiful palettes")

    # Sidebar for options
    st.sidebar.header("🎨 Palette Settings")
    num_colors = st.sidebar.slider("Number of Colors", min_value=3, max_value=10, value=5)
    sort_by = st.sidebar.selectbox("Sort Colors By", ["Frequency", "Hue", "Lightness", "Saturation"])

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=['jpg', 'jpeg', 'png', 'bmp', 'tiff'],
        accept_multiple_files=False
    )

    if uploaded_file is not None:
        # Load image
        image = Image.open(uploaded_file)
        
        # Create two-column layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(image, caption="Uploaded Image", use_column_width=True)
        
        with col2:
            with st.spinner("Analyzing image colors..."):
                # Get dominant colors
                dominant_colors = get_dominant_colors(image, num_colors)
                
                # Convert to hex colors
                hex_colors = [rgb_to_hex(color) for color in dominant_colors]
                
                # Create palette visualization
                fig = create_palette_visualization(dominant_colors, hex_colors)
                st.pyplot(fig, bbox_inches='tight')
                
                # Display color information
                st.markdown("### 🌈 Color Details")
                
                for i, color in enumerate(dominant_colors):
                    color_info = get_color_info(color)
                    
                    # Create color card
                    color_card = f"""
                    <div style="
                        display: flex;
                        align-items: center;
                        padding: 10px;
                        margin: 5px 0;
                        border-radius: 8px;
                        background-color: {color_info['HEX']};
                        color: {'white' if sum(color) < 384 else 'black'};
                        border: 1px solid #ddd;
                    ">
                        <div style="
                            width: 40px;
                            height: 40px;
                            background-color: {color_info['HEX']};
                            border: 2px solid #333;
                            border-radius: 50%;
                            margin-right: 15px;
                        "></div>
                        <div>
                            <strong>Color {i+1}: {color_info['HEX']}</strong><br>
                            <small>{color_info['RGB']} | Sat: {color_info['Saturation %']}%</small><br>
                            <small>{color_info['Brightness Level']} {color_info['Primary Component']}</small>
                        </div>
                    </div>
                    """
                    st.markdown(color_card, unsafe_allow_html=True)

        # Create download section
        st.markdown("### 💾 Export Palette")
        
        # Create tabs for different export formats
        export_tab1, export_tab2, export_tab3 = st.tabs(["CSS Variables", "HEX Codes", "Palette Info"])
        
        with export_tab1:
            css_vars = "\n".join([f"  --color-{i+1}: {hex_color};" for i, hex_color in enumerate(hex_colors)])
            css_code = f":root {{\n{css_vars}\n}}"
            st.code(css_code, language='css')
        
        with export_tab2:
            hex_list = "\n".join(hex_colors)
            st.code(hex_list)
        
        with export_tab3:
            palette_info = {
                "image_name": uploaded_file.name,
                "num_colors": num_colors,
                "colors": [{"hex": color, "rgb": get_color_info(hex_to_rgb(color))["RGB"]} for color in hex_colors]
            }
            st.json(palette_info)

        # Additional color tools
        st.markdown("### 🔧 Color Tools")
        
        # Color contrast checker
        if len(hex_colors) >= 2:
            col_contrast1, col_contrast2 = st.columns(2)
            
            with col_contrast1:
                bg_color = st.selectbox("Background Color", hex_colors, key="bg_color")
            
            with col_contrast2:
                fg_color = st.selectbox("Text Color", hex_colors, key="fg_color")
            
            # Calculate contrast ratio
            def calculate_luminance(hex_color):
                rgb = hex_to_rgb(hex_color)
                r, g, b = [x/255 for x in rgb]
                r = r/12.92 if r <= 0.03928 else pow((r+0.055)/1.055, 2.4)
                g = g/12.92 if g <= 0.03928 else pow((g+0.055)/1.055, 2.4)
                b = b/12.92 if b <= 0.03928 else pow((b+0.055)/1.055, 2.4)
                return 0.2126 * r + 0.7152 * g + 0.0722 * b
            
            lum1 = calculate_luminance(bg_color)
            lum2 = calculate_luminance(fg_color)
            contrast_ratio = (lum1 + 0.05) / (lum2 + 0.05) if lum1 > lum2 else (lum2 + 0.05) / (lum1 + 0.05)
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; color: {fg_color}; padding: 20px; border-radius: 8px; border: 2px solid #333;">
                <h4>Contrast Sample</h4>
                <p>This text demonstrates the color combination.</p>
                <p><strong>Contrast Ratio: {contrast_ratio:.2f}:1</strong></p>
                <p>{'>= 4.5:1 recommended for normal text' if contrast_ratio >= 4.5 else 'Contrast ratio should be >= 4.5:1 for accessibility'}</p>
            </div>
            """, unsafe_allow_html=True)

    else:
        # Show example if no file uploaded
        st.info("👆 Upload an image file to extract its color palette")
        
        with st.expander("🎨 About Color Palettes"):
            st.write("""
            **Color palettes** extracted from images can help you:
            
            - Match your website/blog colors to your images
            - Create cohesive design themes
            - Find accent colors for your content
            - Ensure accessibility with proper contrast ratios
            - Generate CSS variables for consistent styling
            
            The tool uses K-means clustering to identify the most dominant colors in your image.
            """)

if __name__ == "__main__":
    main()