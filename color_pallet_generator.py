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

def get_dominant_colors(image, num_colors=5, sort_by="Frequency"):
    if image.mode != 'RGB':
        image = image.convert('RGB')
    image = image.resize((150, 150))
    img_array = np.array(image).reshape((-1, 3))
    kmeans = KMeans(n_clusters=num_colors, random_state=42, n_init=10).fit(img_array)
    colors = kmeans.cluster_centers_.astype(int)
    sorted_labels = sorted(Counter(kmeans.labels_).items(), key=lambda x: x[1], reverse=True)
    dominant_colors = [colors[label] for label, count in sorted_labels]

    if sort_by == "Hue":
        dominant_colors.sort(key=lambda c: colorsys.rgb_to_hls(c[0]/255, c[1]/255, c[2]/255)[0])
    elif sort_by == "Lightness":
        dominant_colors.sort(key=lambda c: colorsys.rgb_to_hls(c[0]/255, c[1]/255, c[2]/255)[1])
    elif sort_by == "Saturation":
        dominant_colors.sort(key=lambda c: colorsys.rgb_to_hls(c[0]/255, c[1]/255, c[2]/255)[2])
    return dominant_colors

def calculate_luminance(hex_color):
    rgb = hex_to_rgb(hex_color)
    res = []
    for x in rgb:
        x /= 255.0
        res.append(x/12.92 if x <= 0.03928 else pow((x+0.055)/1.055, 2.4))
    return 0.2126 * res[0] + 0.7152 * res[1] + 0.0722 * res[2]

# --- MAIN APP ---

def main():
    st.set_page_config(page_title="Color Palette Generator", page_icon="🎨", layout="wide")
    
    # Initialize Session State for History
    if 'palette_history' not in st.session_state:
        st.session_state.palette_history = []

    st.title("🎨 Color Palette Generator")
    st.subheader("Extract dominant colors, explore color theory, and track your history")

    st.sidebar.header("🎨 Palette Settings")
    num_colors = st.sidebar.slider("Number of Colors", 3, 10, 5)
    sort_by = st.sidebar.selectbox("Sort Colors By", ["Frequency", "Hue", "Lightness", "Saturation"])
    
    if st.sidebar.button("🗑️ Clear History"):
        st.session_state.palette_history = []
        st.rerun()

    uploaded_file = st.file_uploader("Choose an image", type=['jpg', 'jpeg', 'png', 'bmp'])

    if uploaded_file:
        image = Image.open(uploaded_file)
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(image, caption="Original Image", use_container_width=True)
        
        with col2:
            with st.spinner("Analyzing..."):
                dominant_colors = get_dominant_colors(image, num_colors, sort_by)
                hex_colors = [rgb_to_hex(c) for c in dominant_colors]
                
                # Save to history if not duplicate of the last entry
                palette_data = {"name": uploaded_file.name, "colors": hex_colors}
                if not st.session_state.palette_history or st.session_state.palette_history[-1] != palette_data:
                    st.session_state.palette_history.append(palette_data)

                # Palette Visualization
                fig, ax = plt.subplots(figsize=(12, 2))
                for i, h in enumerate(hex_colors):
                    ax.add_patch(patches.Rectangle((i, 0), 1, 1, facecolor=h))
                    ax.text(i+0.5, 0.5, h, ha='center', va='center', fontweight='bold', 
                            color='white' if sum(hex_to_rgb(h)) < 384 else 'black')
                ax.set_xlim(0, len(hex_colors)); ax.set_ylim(0, 1); ax.axis('off')
                st.pyplot(fig, bbox_inches='tight')
                
                # Download
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=300, bbox_inches='tight')
                st.download_button("💾 Download Palette PNG", buf.getvalue(), "palette.png", "image/png")

                st.markdown("### 🌈 Color Theory Suggestions")
                for i, color in enumerate(dominant_colors):
                    h_hex = rgb_to_hex(color)
                    comp_hex = get_complementary_color(color)
                    ana = get_analogous_colors(color)
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; padding: 10px; border-radius: 10px; margin-bottom: 10px;">
                        <div style="display: flex; align-items: center; gap: 15px;">
                            <div style="width: 30px; height: 30px; background:{h_hex}; border-radius: 50%; border: 1px solid #333;"></div>
                            <strong>{h_hex}</strong>
                        </div>
                        <div style="display: flex; gap: 10px; margin-top: 10px;">
                            <div style="flex: 1; text-align: center; background:{comp_hex}; border-radius: 4px; color:{'white' if sum(hex_to_rgb(comp_hex))<384 else 'black'}; font-size: 10px;">Comp: {comp_hex}</div>
                            <div style="flex: 1; text-align: center; background:{ana[0]}; border-radius: 4px; color:{'white' if sum(hex_to_rgb(ana[0]))<384 else 'black'}; font-size: 10px;">Ana 1: {ana[0]}</div>
                            <div style="flex: 1; text-align: center; background:{ana[1]}; border-radius: 4px; color:{'white' if sum(hex_to_rgb(ana[1]))<384 else 'black'}; font-size: 10px;">Ana 2: {ana[1]}</div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                    st.code(h_hex)

        # --- PALETTE HISTORY SECTION ---
        st.divider()
        st.markdown("### 📜 Palette History")
        if st.session_state.palette_history:
            for idx, history in enumerate(reversed(st.session_state.palette_history)):
                with st.expander(f"Palette from: {history['name']} (Record {len(st.session_state.palette_history) - idx})"):
                    cols = st.columns(len(history['colors']))
                    for i, color in enumerate(history['colors']):
                        cols[i].markdown(f"""
                        <div style="background-color:{color}; height:50px; border-radius:5px; border:1px solid #ddd; display:flex; align-items:center; justify-content:center; color:{'white' if sum(hex_to_rgb(color)) < 384 else 'black'}; font-size:10px; font-weight:bold;">
                        {color}
                        </div>""", unsafe_allow_html=True)

        # --- COLOR TOOLS SECTION ---
        st.divider()
        st.markdown("### 🔧 Color Tools")
        if len(hex_colors) >= 2:
            c1, c2 = st.columns(2)
            bg = c1.selectbox("Background Color", hex_colors, index=0)
            fg = c2.selectbox("Text Color", hex_colors, index=min(1, len(hex_colors)-1))
            
            l1, l2 = calculate_luminance(bg), calculate_luminance(fg)
            ratio = (l1 + 0.05) / (l2 + 0.05) if l1 > l2 else (l2 + 0.05) / (l1 + 0.05)
            
            st.markdown(f"""
            <div style="background-color: {bg}; color: {fg}; padding: 20px; border-radius: 8px; border: 1px solid #333; text-align: center;">
                <h4>Contrast Preview</h4>
                <p style="font-size: 1.2em;">The quick brown fox jumps over the lazy dog.</p>
                <p><strong>Contrast Ratio: {ratio:.2f}:1</strong></p>
                <p>{"✅ Meets WCAG AA (4.5:1)" if ratio >= 4.5 else "⚠️ Low Contrast"}</p>
            </div>""", unsafe_allow_html=True)

    else:
        st.info("👆 Upload an image file to extract its color palette")
        with st.expander("🎨 About Color Palettes"):
            st.write("""
            **Features included:**
            - **K-Means Clustering:** ML-driven color extraction.
            - **Sorting Engine:** View palettes by Frequency, Hue, Lightness, or Saturation.
            - **History Tracking:** Compare colors from different image uploads side-by-side.
            - **Accessibility Tool:** Built-in WCAG contrast ratio checker.
            """)

if __name__ == "__main__":
    main()


st.sidebar.markdown("---")
st.sidebar.markdown("Created by **[Your Name]** 🇰🇭")
