import streamlit as st
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import Counter
import colorsys
import io

# --- HELPER FUNCTIONS ---

def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_complementary_color(rgb):
    r, g, b = [x/255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    comp_h = (h + 0.5) % 1.0
    comp_rgb = colorsys.hls_to_rgb(comp_h, l, s)
    return rgb_to_hex(tuple(int(x*255) for x in comp_rgb))

def get_analogous_colors(rgb):
    r, g, b = [x/255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    ana_1 = (h + 0.083) % 1.0
    ana_2 = (h - 0.083) % 1.0
    rgb1 = colorsys.hls_to_rgb(ana_1, l, s)
    rgb2 = colorsys.hls_to_rgb(ana_2, l, s)
    return [rgb_to_hex(tuple(int(x*255) for x in rgb1)), rgb_to_hex(tuple(int(x*255) for x in rgb2))]

def get_dominant_colors_v2(image, num_colors=5, sort_by="Frequency"):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image = image.resize((150, 150))
    img_array = np.array(image).reshape((-1, 3))
    total_pixels = len(img_array)
    
    kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10).fit(img_array)
    colors = kmeans.cluster_centers_.astype(int)
    label_counts = Counter(kmeans.labels_)
    
    color_data = []
    for label, count in label_counts.items():
        percentage = (count / total_pixels) * 100
        color_data.append({
            'rgb': tuple(colors[label]),
            'hex': rgb_to_hex(colors[label]),
            'percent': percentage
        })
    
    # Primary sort for 60-30-10 logic
    color_data.sort(key=lambda x: x['percent'], reverse=True)
    
    if sort_by != "Frequency":
        if sort_by == "Hue":
            color_data.sort(key=lambda x: colorsys.rgb_to_hls(x['rgb'][0]/255, x['rgb'][1]/255, x['rgb'][2]/255)[0])
        elif sort_by == "Lightness":
            color_data.sort(key=lambda x: colorsys.rgb_to_hls(x['rgb'][0]/255, x['rgb'][1]/255, x['rgb'][2]/255)[1])
        elif sort_by == "Saturation":
            color_data.sort(key=lambda x: colorsys.rgb_to_hls(x['rgb'][0]/255, x['rgb'][1]/255, x['rgb'][2]/255)[2])
            
    return color_data

def calculate_luminance(hex_color):
    rgb = hex_to_rgb(hex_color)
    res = []
    for x in rgb:
        x /= 255.0
        res.append(x/12.92 if x <= 0.03928 else pow((x+0.055)/1.055, 2.4))
    return 0.2126 * res[0] + 0.7152 * res[1] + 0.0722 * res[2]

# --- MAIN APP ---

def main():
    st.set_page_config(page_title="Color Palette Generator v2.0", page_icon="🎨", layout="wide")
    
    if 'palette_history' not in st.session_state:
        st.session_state.palette_history = []

    st.title("🎨 Color Palette Generator v2.0")
    st.subheader("Professional Interior & Exterior Design Suite")

    st.sidebar.header("🎨 Settings")
    num_colors = st.sidebar.slider("Number of Colors", 3, 10, 5)
    sort_by = st.sidebar.selectbox("Sort Colors By", ["Frequency", "Hue", "Lightness", "Saturation"])
    
    if st.sidebar.button("🗑️ Clear History"):
        st.session_state.palette_history = []
        st.rerun()

    uploaded_file = st.file_uploader("Upload inspiration image", type=['jpg', 'jpeg', 'png', 'bmp'])

    if uploaded_file:
        image = Image.open(uploaded_file)
        col1, col2 = st.columns([1, 2])
        
        with col1:
            # Fixed deprecation: use_container_width instead of use_column_width
            st.image(image, caption="Source Image", use_container_width=True)
        
        with col2:
            with st.spinner("Analyzing Design DNA..."):
                color_data = get_dominant_colors_v2(image, num_colors, sort_by)
                hex_colors = [c['hex'] for c in color_data]
                
                # Update History
                palette_entry = {"name": uploaded_file.name, "colors": hex_colors}
                if not st.session_state.palette_history or st.session_state.palette_history[-1] != palette_entry:
                    st.session_state.palette_history.append(palette_entry)

                # Palette Display
                fig, ax = plt.subplots(figsize=(12, 2))
                for i, h in enumerate(hex_colors):
                    ax.add_patch(patches.Rectangle((i, 0), 1, 1, facecolor=h))
                    ax.text(i+0.5, 0.5, h, ha='center', va='center', fontweight='bold', 
                            color='white' if sum(hex_to_rgb(h)) < 384 else 'black')
                ax.set_xlim(0, len(hex_colors)); ax.set_ylim(0, 1); ax.axis('off')
                st.pyplot(fig, bbox_inches='tight')
                
                # Export Button
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
                st.download_button("💾 Export Palette PNG", buf.getvalue(), f"palette_{uploaded_file.name}.png", "image/png")

                # 60-30-10 Rule Table
                st.markdown("### 📐 Interior Design Balance (60-30-10)")
                table_html = """<table style='width:100%; border-collapse: collapse;'>
                <tr style='background-color: #f0f2f6;'><th>Role</th><th>Color</th><th>Weight</th><th>Application</th></tr>"""
                for i, c in enumerate(color_data):
                    role = "Dominant" if i == 0 else "Secondary" if i == 1 else "Accent"
                    app = "Walls/Floors" if i == 0 else "Furniture" if i == 1 else "Decor"
                    table_html += f"<tr><td>{role}</td><td><div style='background:{c['hex']}; width:20px; height:20px; display:inline-block;'></div> {c['hex']}</td><td>{c['percent']:.1f}%</td><td>{app}</td></tr>"
                st.markdown(table_html + "</table>", unsafe_allow_html=True)

        st.divider()
        st.markdown("### 🌈 Theory & Accessibility")
        t_cols = st.columns(min(len(color_data), 4))
        for i, c in enumerate(color_data[:4]):
            with t_cols[i]:
                comp = get_complementary_color(c['rgb'])
                st.markdown(f"**Base: {c['hex']}**")
                st.markdown(f"<div style='background:{comp}; height:30px; border-radius:5px; text-align:center; color:white;'>Comp: {comp}</div>", unsafe_allow_html=True)
                st.code(c['hex'])

        if st.session_state.palette_history:
            with st.expander("📜 View Palette History"):
                for h in reversed(st.session_state.palette_history):
                    st.write(f"Source: {h['name']}")
                    cols = st.columns(len(h['colors']))
                    for i, color in enumerate(h['colors']):
                        cols[i].markdown(f"<div style='background:{color}; height:40px; border-radius:5px;'></div>", unsafe_allow_html=True)

    else:
        st.info("Upload an image to start your v2.0 design analysis.")

if __name__ == "__main__":
    main()
