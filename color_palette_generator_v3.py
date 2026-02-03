import streamlit as st
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from collections import Counter
import colorsys
import io
import google.generativeai as genai

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

def get_dominant_colors_v3(image, num_colors=5, sort_by="Frequency"):
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
    
    color_data.sort(key=lambda x: x['percent'], reverse=True)
    
    if sort_by != "Frequency":
        if sort_by == "Hue":
            color_data.sort(key=lambda x: colorsys.rgb_to_hls(x['rgb'][0]/255, x['rgb'][1]/255, x['rgb'][2]/255)[0])
        elif sort_by == "Lightness":
            color_data.sort(key=lambda x: colorsys.rgb_to_hls(x['rgb'][0]/255, x['rgb'][1]/255, x['rgb'][2]/255)[1])
        elif sort_by == "Saturation":
            color_data.sort(key=lambda x: colorsys.rgb_to_hls(x['rgb'][0]/255, x['rgb'][1]/255, x['rgb'][2]/255)[2])
            
    return color_data

def analyze_materials_with_ai(image, api_key):
    """v3.0 AI Material Analysis Engine"""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3-flash-preview')
        prompt = (
            "You are an Interior Architect. Analyze this image for materials. "
            "List primary textures (e.g., velvet, brushed concrete, wood), "
            "describe if they absorb or reflect light, and suggest one "
            "missing texture (like a thick wool throw) to balance the room."
        )
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        return f"Error connecting to AI: {str(e)}"

# --- MAIN APP ---

def main():
    st.set_page_config(page_title="Color Palette v3.0", page_icon="🏛️", layout="wide")
    
    if 'palette_history' not in st.session_state:
        st.session_state.palette_history = []

    st.title("🏛️ Professional Design Palette v3.0")
    st.subheader("K-Means Precision + AI Material Intelligence")

    # SIDEBAR
    st.sidebar.header("⚙️ Settings")
    num_colors = st.sidebar.slider("Number of Colors", 3, 10, 5)
    sort_by = st.sidebar.selectbox("Sort By", ["Frequency", "Hue", "Lightness", "Saturation"])
    
    st.sidebar.divider()
    st.sidebar.markdown("### 🧠 AI Features")
    st.sidebar.markdown("[Get free Gemini Key](https://aistudio.google.com/app/apikey)")
    api_key = st.sidebar.text_input("Gemini API Key", type="password", help="Your key is never stored on our servers.")
    
    if st.sidebar.button("🗑️ Clear History"):
        st.session_state.palette_history = []
        st.rerun()

    uploaded_file = st.file_uploader("Upload an inspiration photo", type=['jpg', 'jpeg', 'png', 'bmp'])

    if uploaded_file:
        image = Image.open(uploaded_file)
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(image, caption="Inspiration Source", use_container_width=True)
            
            # AI TRIGGER
            if api_key:
                if st.button("🔍 Analyze Material Behavior"):
                    with st.spinner("AI is feeling the textures..."):
                        analysis = analyze_materials_with_ai(image, api_key)
                        st.markdown("---")
                        st.markdown("### 🏛️ AI Material Insight")
                        st.info(analysis)
            else:
                st.warning("Enter an API Key in the sidebar to unlock Material Intelligence.")

        with col2:
            with st.spinner("Calculating Design DNA..."):
                color_data = get_dominant_colors_v3(image, num_colors, sort_by)
                hex_colors = [c['hex'] for c in color_data]
                
                # History Save
                palette_entry = {"name": uploaded_file.name, "colors": hex_colors}
                if not st.session_state.palette_history or st.session_state.palette_history[-1] != palette_entry:
                    st.session_state.palette_history.append(palette_entry)

                # Palette Display
                fig, ax = plt.subplots(figsize=(12, 2.5))
                for i, h in enumerate(hex_colors):
                    ax.add_patch(patches.Rectangle((i, 0), 1, 1, facecolor=h))
                    # Contrast detection for labels
                    rgb = hex_to_rgb(h)
                    label_color = 'white' if sum(rgb) < 384 else 'black'
                    ax.text(i+0.5, 0.5, h, ha='center', va='center', fontweight='bold', color=label_color)
                ax.set_xlim(0, len(hex_colors)); ax.set_ylim(0, 1); ax.axis('off')
                st.pyplot(fig, bbox_inches='tight')

                # 60-30-10 Rule Table
                st.markdown("### 📐 The 60-30-10 Design Rule")
                table_html = "<table style='width:100%; border-collapse: collapse;'> <tr style='background-color: #f0f2f6;'><th>Role</th><th>Color</th><th>Weight</th><th>Application</th></tr>"
                for i, c in enumerate(color_data):
                    role = "Dominant" if i == 0 else "Secondary" if i == 1 else "Accent"
                    app = "Walls / Large Rugs" if i == 0 else "Furniture / Curtains" if i == 1 else "Decor / Pillows"
                    table_html += f"<tr><td><strong>{role}</strong></td><td><div style='background:{c['hex']}; width:15px; height:15px; display:inline-block; border:1px solid #000;'></div> {c['hex']}</td><td>{c['percent']:.1f}%</td><td>{app}</td></tr>"
                st.markdown(table_html + "</table>", unsafe_allow_html=True)

        st.divider()
        st.markdown("### 📜 Palette History")
        if st.session_state.palette_history:
            for h in reversed(st.session_state.palette_history):
                with st.expander(f"Record: {h['name']}"):
                    cols = st.columns(len(h['colors']))
                    for i, color in enumerate(h['colors']):
                        cols[i].markdown(f"<div style='background:{color}; height:35px; border-radius:4px;'></div>", unsafe_allow_html=True)
                        cols[i].code(color)

    else:
        st.info("Upload an image to unlock v3.0 analysis.")

if __name__ == "__main__":
    main()
