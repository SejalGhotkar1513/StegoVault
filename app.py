import streamlit as st
from PIL import Image
import io

st.set_page_config(
    page_title="StegoVault | Image Steganography",
    page_icon="🔐",
    layout="wide",
)

st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1200px;}
.hero{padding:2rem 2.2rem;border-radius:24px;background:linear-gradient(135deg,#24143f,#4b256d);color:white;margin-bottom:1.5rem}
.hero h1{font-size:2.7rem;margin-bottom:.3rem}.hero p{font-size:1.05rem;opacity:.9}
.member{padding:.7rem 1rem;border-radius:12px;background:rgba(128,128,128,.08);margin:.35rem 0}
</style>
""", unsafe_allow_html=True)

MAGIC = b"STGV1"

def to_bits(data):
    for byte in data:
        for shift in range(7, -1, -1):
            yield (byte >> shift) & 1

def from_bits(bits):
    out = bytearray()
    for i in range(0, len(bits), 8):
        value = 0
        for bit in bits[i:i+8]:
            value = (value << 1) | bit
        out.append(value)
    return bytes(out)

def encode_image(image, message):
    image = image.convert("RGB")
    pixels = list(image.getdata())

    payload = message.encode("utf-8")
    data = MAGIC + len(payload).to_bytes(4, "big") + payload
    bits = list(to_bits(data))

    capacity = len(pixels) * 3
    if len(bits) > capacity:
        max_bytes = max(0, (capacity - 72) // 8)
        raise ValueError(
            f"Message is too large for this image. Try a shorter message (about {max_bytes:,} bytes maximum)."
        )

    new_pixels = []
    index = 0

    for r, g, b in pixels:
        channels = [r, g, b]
        for c in range(3):
            if index < len(bits):
                channels[c] = (channels[c] & 254) | bits[index]
                index += 1
        new_pixels.append(tuple(channels))

    result = Image.new("RGB", image.size)
    result.putdata(new_pixels)
    return result

def decode_image(image):
    image = image.convert("RGB")

    bits = []
    for r, g, b in image.getdata():
        bits.extend([r & 1, g & 1, b & 1])

    if len(bits) < 72:
        raise ValueError("This image is too small to contain a StegoVault message.")

    header = from_bits(bits[:72])
    if header[:5] != MAGIC:
        raise ValueError(
            "This is not a StegoVault encoded image. Please upload the PNG downloaded from the Encode tab."
        )

    message_length = int.from_bytes(header[5:9], "big")
    available = (len(bits) - 72) // 8

    if message_length > available:
        raise ValueError("The encoded message appears to be damaged or incomplete.")

    message_bytes = from_bits(bits[72:72 + message_length * 8])

    try:
        return message_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("The hidden message could not be decoded correctly.")

st.markdown("""
<div class="hero">
<h1>🔐 StegoVault</h1>
<p>Image Steganography using Least Significant Bit (LSB)</p>
<p>Hide a secret text message inside an image and reveal it later.</p>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🔒 Encode", "🔓 Decode", "ℹ️ About"])

with tab1:
    st.subheader("Hide a secret message")
    col1, col2 = st.columns(2)

    with col1:
        uploaded = st.file_uploader(
            "Upload your original image",
            type=["png", "jpg", "jpeg"],
            key="encode_upload"
        )
        if uploaded:
            source = Image.open(uploaded).convert("RGB")
            st.image(source, caption="Original image", use_container_width=True)

    with col2:
        message = st.text_area(
            "Enter your secret message",
            height=180,
            placeholder="Example: This is my hidden message."
        )

        if uploaded and message:
            if st.button("🔐 Encode Message", type="primary", use_container_width=True):
                try:
                    encoded = encode_image(source, message)
                    buffer = io.BytesIO()
                    encoded.save(buffer, format="PNG")

                    st.session_state["encoded_bytes"] = buffer.getvalue()
                    st.session_state["encoded_image"] = encoded
                    st.success("✅ Message hidden successfully!")
                except Exception as e:
                    st.error(str(e))

    if "encoded_image" in st.session_state:
        st.divider()
        st.subheader("Your encoded image")
        st.image(
            st.session_state["encoded_image"],
            caption="This is the image you MUST use for decoding",
            use_container_width=True
        )
        st.download_button(
            "⬇️ Download Encoded PNG",
            data=st.session_state["encoded_bytes"],
            file_name="stegovault_encoded.png",
            mime="image/png",
            use_container_width=True
        )
        st.info("⚠️ Decode the downloaded 'stegovault_encoded.png' file — not the original image.")

with tab2:
    st.subheader("Reveal a hidden message")
    st.info("Upload the PNG created by the Encode tab. Do not upload the original image.")

    encoded_upload = st.file_uploader(
        "Upload StegoVault encoded image",
        type=["png", "jpg", "jpeg"],
        key="decode_upload"
    )

    if encoded_upload:
        decode_source = Image.open(encoded_upload).convert("RGB")
        st.image(decode_source, caption="Image to decode", use_container_width=True)

        if st.button("🔓 Decode Message", type="primary"):
            try:
                hidden = decode_image(decode_source)
                st.success("✅ Hidden message found!")
                st.text_area("Decoded message", hidden, height=180)
            except Exception as e:
                st.error(str(e))

with tab3:
    st.subheader("About this project")
    st.write(
        "StegoVault uses LSB (Least Significant Bit) steganography. "
        "The application stores a small identifier, message length, and UTF-8 message "
        "inside the RGB pixel values of the image."
    )

    st.subheader("👥 Group Members")
    for name in ["Dhanshri Ghule", "Purva Atigre", "Sejal Ghotkar", "Siddhi Gaikwad"]:
        st.markdown(f'<div class="member">👤 {name}</div>', unsafe_allow_html=True)

    st.subheader("🧰 Technologies")
    st.write("Python • Streamlit • Pillow • LSB Steganography")

st.markdown("---")
st.markdown(
    "<div style='text-align:center;opacity:.7;'>StegoVault • Academic Mini Project • LSB Image Steganography</div>",
    unsafe_allow_html=True
)
