import streamlit as st
import requests
import xml.etree.ElementTree as ET
import pandas as pd
from io import BytesIO
import concurrent.futures
import time
import json

# Initialize session state for theme
if 'theme' not in st.session_state:
    # Try to load from localStorage
    theme_preference = st.session_state.get('theme_preference', 'light')
    st.session_state.theme = theme_preference

# Page config
st.set_page_config(
    page_title="SitemapSage",
    page_icon="🗺️",
    layout="wide"
)

# Define theme colors
THEMES = {
    'light': {
        'primary': '#1E88E5',
        'background': '#FFFFFF',
        'text': '#333333',
        'secondary': '#757575',
        'success': '#4CAF50',
        'error': '#F44336',
        'card_bg': '#F5F5F5',
    },
    'dark': {
        'primary': '#90CAF9',
        'background': '#121212',
        'text': '#FFFFFF',
        'secondary': '#BDBDBD',
        'success': '#81C784',
        'error': '#E57373',
        'card_bg': '#1E1E1E',
    }
}

# Get current theme colors
theme_colors = THEMES[st.session_state.theme]

# Custom CSS with dynamic theme colors
st.markdown(f"""
    <style>
    /* Base theme */
    .stApp {{
        background-color: {theme_colors['background']};
        color: {theme_colors['text']};
    }}
    
    .main-header {{
        font-size: 2.5rem;
        color: {theme_colors['primary']};
        text-align: center;
        margin-bottom: 2rem;
        transition: color 0.3s ease;
    }}
    
    .subheader {{
        font-size: 1.2rem;
        color: {theme_colors['secondary']};
        text-align: center;
        margin-bottom: 2rem;
    }}
    
    /* Custom Card */
    .custom-card {{
        background-color: {theme_colors['card_bg']};
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }}
    
    .custom-card:hover {{
        transform: translateY(-2px);
    }}
    
    /* Statistics Counter */
    .stat-counter {{
        font-size: 2rem;
        font-weight: bold;
        color: {theme_colors['primary']};
        text-align: center;
        animation: countUp 2s ease-out;
    }}
    
    /* Tooltip */
    .tooltip {{
        position: relative;
        display: inline-block;
    }}
    
    .tooltip .tooltiptext {{
        visibility: hidden;
        background-color: {theme_colors['card_bg']};
        color: {theme_colors['text']};
        text-align: center;
        padding: 5px 10px;
        border-radius: 6px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.3s;
    }}
    
    .tooltip:hover .tooltiptext {{
        visibility: visible;
        opacity: 1;
    }}
    
    /* Status Indicators */
    .status-badge {{
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
        margin: 0 4px;
    }}
    
    .status-healthy {{
        background-color: {theme_colors['success']};
        color: white;
    }}
    
    .status-error {{
        background-color: {theme_colors['error']};
        color: white;
    }}
    
    /* Collapsible Section */
    .collapsible {{
        cursor: pointer;
        padding: 10px;
        background-color: {theme_colors['card_bg']};
        border: none;
        border-radius: 5px;
        margin: 5px 0;
    }}
    
    @keyframes countUp {{
        from {{
            opacity: 0;
            transform: translateY(20px);
        }}
        to {{
            opacity: 1;
            transform: translateY(0);
        }}
    }}
    </style>
    """, unsafe_allow_html=True)

# Sidebar Theme Toggle
with st.sidebar:
    st.title("Settings")
    theme_selector = st.selectbox(
        "Choose Theme",
        ["Light", "Dark"],
        index=0 if st.session_state.theme == 'light' else 1,
        key="theme_selector"
    )
    
    # Update theme when changed
    if theme_selector.lower() != st.session_state.theme:
        st.session_state.theme = theme_selector.lower()
        st.experimental_rerun()

def create_tooltip(text, help_text):
    return f"""
        <div class="tooltip">
            {text}
            <span class="tooltiptext">{help_text}</span>
        </div>
    """

def check_url_health(url):
    try:
        response = requests.head(url, timeout=5)
        return {
            'status_code': response.status_code,
            'is_healthy': 200 <= response.status_code < 400,
            'response_time': response.elapsed.total_seconds()
        }
    except:
        return {
            'status_code': 0,
            'is_healthy': False,
            'response_time': 0
        }

def extract_urls_from_sitemap(sitemap_url):
    # ... (previous extract_urls_from_sitemap code remains the same)
    pass

def create_stat_card(title, value, description):
    return f"""
        <div class="custom-card">
            <h3 style="color: {theme_colors['secondary']};">{title}</h3>
            <div class="stat-counter">{value}</div>
            <p>{description}</p>
        </div>
    """

def main():
    st.markdown("<h1 class='main-header'>🗺️ SitemapSage</h1>", unsafe_allow_html=True)
    st.markdown(create_tooltip(
        "<p class='subheader'>Extract, analyze, and export URLs from any XML sitemap</p>",
        "Process single or multiple sitemaps and get detailed URL analysis"
    ), unsafe_allow_html=True)
    
    # Input method selector in a custom card
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    input_method = st.radio(
        "Choose input method:",
        ["Single URL", "Multiple URLs", "Upload File"]
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    sitemap_urls = []
    
    # Input section in a custom card
    st.markdown('<div class="custom-card">', unsafe_allow_html=True)
    if input_method == "Single URL":
        url = st.text_input(
            create_tooltip("Enter XML Sitemap URL:", "Enter the full URL including http:// or https://"),
            placeholder="https://example.com/sitemap.xml"
        )
        if url:
            sitemap_urls = [url]
            
    elif input_method == "Multiple URLs":
        urls_text = st.text_area(
            create_tooltip("Enter multiple sitemap URLs (one per line):", "Each URL should be on a new line"),
            placeholder="https://example1.com/sitemap.xml\nhttps://example2.com/sitemap.xml"
        )
        if urls_text:
            sitemap_urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
            
    else:  # Upload File
        uploaded_file = st.file_uploader(
            create_tooltip("Upload a text file with sitemap URLs", "File should contain one URL per line"),
            type=['txt']
        )
        if uploaded_file:
            content = uploaded_file.getvalue().decode()
            sitemap_urls = [url.strip() for url in content.split('\n') if url.strip()]
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process button
    if st.button("🔍 Process Sitemaps", use_container_width=True):
        if sitemap_urls:
            # Progress tracking
            progress_bar = st.progress(0)
            status_container = st.empty()
            
            # Statistics containers
            col1, col2, col3 = st.columns(3)
            stats_containers = {
                'processed': col1.empty(),
                'success': col2.empty(),
                'urls': col3.empty()
            }
            
            # Initialize results storage
            all_results = pd.DataFrame()
            total_urls = 0
            successful_sitemaps = 0
            failed_sitemaps = 0
            
            # Process sitemaps with concurrent execution
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {executor.submit(extract_urls_from_sitemap, url): url for url in sitemap_urls}
                
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    result = future.result()
                    progress = (i + 1) / len(sitemap_urls)
                    progress_bar.progress(progress)
                    
                    # Update statistics with animation
                    stats_containers['processed'].markdown(
                        create_stat_card("Processed", f"{i + 1}/{len(sitemap_urls)}", "Sitemaps analyzed"),
                        unsafe_allow_html=True
                    )
                    stats_containers['success'].markdown(
                        create_stat_card("Success Rate", f"{(successful_sitemaps / (i + 1)) * 100:.1f}%", "Successfully processed"),
                        unsafe_allow_html=True
                    )
                    stats_containers['urls'].markdown(
                        create_stat_card("Total URLs", f"{total_urls:,}", "URLs discovered"),
                        unsafe_allow_html=True
                    )
                    
                    if not result.empty:
                        successful_sitemaps += 1
                        total_urls += len(result)
                        all_results = pd.concat([all_results, result], ignore_index=True)
                    else:
                        failed_sitemaps += 1
            
            # Display results in collapsible sections
            if not all_results.empty:
                st.markdown("<h2>Results</h2>", unsafe_allow_html=True)
                
                # URL Health Check (sample of URLs)
                with st.expander("URL Health Status (Sample)", expanded=True):
                    sample_urls = all_results['URL'].sample(min(5, len(all_results)))
                    for url in sample_urls:
                        health = check_url_health(url)
                        status_class = "status-healthy" if health['is_healthy'] else "status-error"
                        st.markdown(f"""
                            <div class="custom-card">
                                <div>{url}</div>
                                <span class="status-badge {status_class}">
                                    Status: {health['status_code']}
                                </span>
                                <span class="status-badge">
                                    Response Time: {health['response_time']:.2f}s
                                </span>
                            </div>
                        """, unsafe_allow_html=True)
                
                # Detailed Results
                with st.expander("Detailed Results", expanded=False):
                    st.dataframe(all_results, height=400)
                
                # Export Options
                with st.expander("Export Options", expanded=True):
                    col1, col2 = st.columns(2)
                    
                    # CSV export
                    csv = all_results.to_csv(index=False).encode('utf-8')
                    col1.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name="sitemap_urls.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                    
                    # Excel export
                    buffer = BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        all_results.to_excel(writer, index=False, sheet_name='URLs')
                    excel_data = buffer.getvalue()
                    col2.download_button(
                        label="📊 Download Excel",
                        data=excel_data,
                        file_name="sitemap_urls.xlsx",
                        mime="application/vnd.ms-excel",
                        use_container_width=True
                    )
        else:
            st.warning("⚠️ Please provide at least one sitemap URL")
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"<p style='text-align: center; color: {theme_colors['secondary']};'>Made with ❤️ by SitemapSage</p>",
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
