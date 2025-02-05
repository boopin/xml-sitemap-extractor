import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from io import StringIO

# Function to extract URLs from an XML sitemap
def extract_urls_from_sitemap(sitemap_url):
    response = requests.get(sitemap_url)
    soup = BeautifulSoup(response.content, 'xml')
    urls = [loc.text for loc in soup.find_all('loc')]
    return urls

# Streamlit app
def main():
    st.title("XML Sitemap URL Extractor")
    
    # Input for the XML sitemap URL
    sitemap_url = st.text_input("Enter the XML Sitemap URL:")
    
    if sitemap_url:
        st.write("Extracting URLs from the sitemap...")
        urls = extract_urls_from_sitemap(sitemap_url)
        
        if urls:
            st.success(f"Found {len(urls)} URLs!")
            
            # Display the URLs in a DataFrame
            df = pd.DataFrame(urls, columns=["URL"])
            st.write(df)
            
            # Export options
            st.subheader("Export Options")
            export_format = st.radio("Select export format:", ("CSV", "XLS"))
            
            if export_format == "CSV":
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="sitemap_urls.csv",
                    mime="text/csv",
                )
            elif export_format == "XLS":
                output = StringIO()
                df.to_excel(output, index=False, engine="openpyxl")
                st.download_button(
                    label="Download XLS",
                    data=output.getvalue(),
                    file_name="sitemap_urls.xlsx",
                    mime="application/vnd.ms-excel",
                )
        else:
            st.error("No URLs found in the sitemap.")

if __name__ == "__main__":
    main()
