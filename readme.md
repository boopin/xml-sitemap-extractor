# Sitemap URL Extractor

A Streamlit web application that extracts URLs from XML sitemaps and exports them to CSV or Excel format. This tool supports both regular sitemaps and sitemap indexes, making it easy to extract URLs from any website's sitemap.

## Features

- Extract URLs from XML sitemaps
- Support for sitemap index files (recursive extraction)
- Extract last modified dates when available
- Interactive data table display
- Export to CSV or Excel formats
- Clean and simple user interface
- Error handling for invalid URLs or malformed XML

## Demo

You can access the live demo here: [Your Streamlit Cloud URL]

## Installation

1. Clone the repository:
```bash
git clone https://github.com/[your-username]/sitemap-extractor.git
cd sitemap-extractor
```

2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Local Development

To run the application locally:
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## Deployment

This application can be easily deployed to Streamlit Cloud:

1. Fork this repository to your GitHub account
2. Visit [share.streamlit.io](https://share.streamlit.io)
3. Sign in with your GitHub account
4. Deploy the application by selecting your forked repository

## Usage

1. Enter the URL of an XML sitemap in the input field
2. Click "Extract URLs" to process the sitemap
3. View the extracted URLs in the interactive table
4. Download the results in either CSV or Excel format

## File Structure

```
sitemap-extractor/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md          # Project documentation
```

## Dependencies

- Python 3.8+
- Streamlit
- Pandas
- Requests
- XlsxWriter
- python-dotenv

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
