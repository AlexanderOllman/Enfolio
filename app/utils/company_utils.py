import requests
import os
import json
import time
import re
from werkzeug.utils import secure_filename
from urllib.parse import urlencode, quote
import wikipediaapi
from bs4 import BeautifulSoup

class CompanySearch:
    def __init__(self, api_key=None):
        # Use provided API key or get from environment variable for Clearbit or other API
        self.api_key = api_key or os.environ.get("COMPANY_API_KEY")
        
        # Create a basic list of top companies for when no API key is available
        # This will be used as fallback when the user starts typing
        self.common_companies = [
            {"name": "Apple", "domain": "apple.com"},
            {"name": "Google", "domain": "google.com"},
            {"name": "Microsoft", "domain": "microsoft.com"},
            {"name": "Amazon", "domain": "amazon.com"},
            {"name": "Meta", "domain": "meta.com"},
            {"name": "Facebook", "domain": "facebook.com"},
            {"name": "IBM", "domain": "ibm.com"},
            {"name": "Intel", "domain": "intel.com"},
            {"name": "Cisco", "domain": "cisco.com"},
            {"name": "Oracle", "domain": "oracle.com"},
            {"name": "Adobe", "domain": "adobe.com"},
            {"name": "Salesforce", "domain": "salesforce.com"},
            {"name": "Netflix", "domain": "netflix.com"},
            {"name": "Tesla", "domain": "tesla.com"},
            {"name": "HP", "domain": "hp.com"},
            {"name": "Hewlett Packard Enterprise", "domain": "hpe.com"},
            {"name": "Dell", "domain": "dell.com"},
            {"name": "Sony", "domain": "sony.com"},
            {"name": "Samsung", "domain": "samsung.com"},
            {"name": "Twitter", "domain": "twitter.com"},
            {"name": "Nvidia", "domain": "nvidia.com"},
            {"name": "AMD", "domain": "amd.com"},
            {"name": "Qualcomm", "domain": "qualcomm.com"},
            {"name": "Uber", "domain": "uber.com"},
            {"name": "Airbnb", "domain": "airbnb.com"},
            {"name": "Slack", "domain": "slack.com"},
            {"name": "Shopify", "domain": "shopify.com"},
            {"name": "PayPal", "domain": "paypal.com"},
            {"name": "eBay", "domain": "ebay.com"},
            {"name": "Spotify", "domain": "spotify.com"},
        ]
    
    def search_companies(self, query):
        """
        Search for companies by name using multiple approaches
        """
        if not query or len(query.strip()) < 2:
            return []
        
        # Filter common companies list first
        query_lower = query.lower()
        filtered_companies = [
            company for company in self.common_companies
            if query_lower in company["name"].lower() or query_lower in company["domain"].lower()
        ]
        
        # If we have results from the common companies, return those
        if filtered_companies:
            return filtered_companies
        
        # If Clearbit API key is available, try using their Autocomplete API
        if self.api_key:
            try:
                # Clearbit Company Autocomplete API (requires API key)
                clearbit_url = "https://autocomplete.clearbit.com/v1/companies/suggest"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                params = {"query": query}
                
                response = requests.get(clearbit_url, headers=headers, params=params)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                print(f"Clearbit API error: {str(e)}")
        
        # Try searching on Wikipedia
        wiki_results = self._search_wikipedia(query)
        if wiki_results:
            return wiki_results
            
        # Try searching for LinkedIn company references
        linkedin_results = self._search_with_linkedin(query)
        if linkedin_results:
            return linkedin_results
        
        # Check if query looks like it's trying to find a company
        # This helps prevent random non-company results
        company_indicators = ['company', 'inc', 'corp', 'ltd', 'llc', 'technology', 'systems', 
                             'solutions', 'group', 'enterprise', 'global', 'international',
                             'software', 'media', 'consulting', 'services']
                             
        query_words = query_lower.split()
        likely_company_query = any(word in company_indicators for word in query_words)
        
        # Search for domain-based matches
        domain_matches = self._search_domain_matches(query)
        if domain_matches:
            return domain_matches
        
        # Only generate potential companies if the query might actually be company-related
        # or if it's a short, clear business name (typically 1-3 words)
        if likely_company_query or (len(query_words) <= 3 and len(query) >= 3):
            # Fallback method: Generate a list of potential companies
            # This is a very simplistic approach but provides a better UX than returning empty results
            companies = []
            search_terms = [
                f"{query}",
                f"{query} Inc",
                f"{query} Corporation",
                f"{query} Technologies"
            ]
            
            for term in search_terms:
                # Create a plausible domain from the company name
                domain = self._extract_domain(term)
                companies.append({
                    "name": term,
                    "domain": domain
                })
            
            return companies[:3]  # Limit to 3 results to reduce noise
        
        # If no results and query doesn't look like a company query, return empty list
        return []
    
    def _search_wikipedia(self, query):
        """
        Search Wikipedia for company information
        """
        try:
            # Initialize the Wikipedia API
            wiki_wiki = wikipediaapi.Wikipedia('Enfolio App (info@enfolio.app)', 'en')
            
            # We'll need to use the search function from the requests module since
            # wikipediaapi doesn't have a built-in search function
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": f"{query} company",
                "srnamespace": 0,
                "srlimit": 5
            }
            
            search_response = requests.get(search_url, params=search_params)
            if search_response.status_code != 200:
                return []
                
            search_data = search_response.json()
            if 'query' not in search_data or 'search' not in search_data['query']:
                return []
                
            # Extract the page titles from the search results
            search_results = [item['title'] for item in search_data['query']['search']]
            
            if not search_results:
                return []
            
            companies = []
            query_lower = query.lower()
            
            for page_title in search_results:
                try:
                    # Get the page from Wikipedia API
                    page = wiki_wiki.page(page_title)
                    
                    # Skip if page doesn't exist
                    if not page.exists():
                        continue
                    
                    # Get a summary of the page
                    extract = page.summary
                    
                    # Skip if it doesn't appear to be a company
                    company_keywords = ['company', 'corporation', 'enterprise', 'firm', 'business', 
                                      'organization', 'incorporated', 'limited', 'ltd', 'inc', 
                                      'llc', 'technologies', 'group', 'systems', 'solutions']
                    
                    is_company = False
                    for term in company_keywords:
                        if term in extract.lower() or term in page_title.lower():
                            is_company = True
                            break
                            
                    if not is_company:
                        continue
                    
                    # Extract all potential domains from the page text
                    website_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z0-9-.]{2,})'
                    website_matches = re.findall(website_pattern, page.text)
                    
                    found_domain = None
                    
                    if website_matches:
                        # First look for domains containing the search query
                        for match in website_matches:
                            # Skip non-company domains
                            if any(match.endswith(suffix) for suffix in [
                                '.edu', '.gov', '.org', '.int', '.mil', '.example.com', 
                                'wikipedia.org', 'google.com'
                            ]):
                                continue
                                
                            # Prioritize domain that contains the search query
                            if query_lower in match.lower():
                                found_domain = match
                                break
                                
                        # If no domain with search query, use first valid domain
                        if not found_domain:
                            for match in website_matches:
                                if not any(match.endswith(suffix) for suffix in [
                                    '.edu', '.gov', '.org', '.int', '.mil', '.example.com', 
                                    'wikipedia.org', 'google.com'
                                ]):
                                    found_domain = match
                                    break
                    
                    # If no domain found, create one from the page title
                    if not found_domain:
                        found_domain = self._extract_domain(page_title)
                    
                    # Check if the domain contains the search query
                    has_query_in_domain = query_lower in found_domain.lower()
                    
                    # Add confidence level based on query-domain match
                    confidence = "high" if has_query_in_domain else "medium"
                    
                    companies.append({
                        "name": page_title,
                        "domain": found_domain,
                        "confidence": confidence
                    })
                    
                    # Prioritize results where the domain contains the search query
                    if has_query_in_domain:
                        # Move this result to the front of the list
                        companies.insert(0, companies.pop())
                    
                    # Limit to 3 results for better UX
                    if len(companies) >= 3:
                        break
                        
                except Exception as e:
                    print(f"Error processing Wikipedia page {page_title}: {str(e)}")
                    continue
            
            return companies
            
        except Exception as e:
            print(f"Wikipedia search error: {str(e)}")
            return []
    
    def _search_with_linkedin(self, query):
        """
        Search for LinkedIn company pages via DuckDuckGo
        """
        try:
            # DDG search focused on LinkedIn company pages
            ddg_url = "https://duckduckgo.com/html/"
            
            # Use specific search operators to improve accuracy
            search_query = f'"{query}" site:linkedin.com/company'
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            params = {
                "q": search_query
            }
            
            response = requests.get(ddg_url, headers=headers, params=params)
            
            if response.status_code != 200:
                return []
            
            # Parse the HTML response to extract LinkedIn company page URLs
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all search result links
            links = soup.select('.result__url')
            
            companies = []
            company_names = set()  # To track unique companies
            query_lower = query.lower()
            
            for link in links:
                url_text = link.get_text()
                
                # Filter for LinkedIn company pages
                if 'linkedin.com/company/' in url_text:
                    try:
                        # Extract company name from URL
                        # Pattern: linkedin.com/company/company-name
                        company_slug = url_text.split('linkedin.com/company/')[1].split('/')[0]
                        
                        # Convert URL-friendly format to readable name
                        company_name = ' '.join(company_slug.split('-')).title()
                        
                        # Avoid duplicates
                        if company_name.lower() in company_names:
                            continue
                            
                        # Generate a domain based on company name
                        domain = self._extract_domain(company_name)
                        
                        # Check if the search query appears in the domain
                        query_in_domain = query_lower in domain.lower()
                        
                        # First, verify relation between company name and query
                        name_related = False
                        query_words = query_lower.split()
                        
                        # Check if any query word is in company name
                        if any(word in company_name.lower() for word in query_words):
                            name_related = True
                        
                        # If query is in domain OR name is related, include the result
                        if query_in_domain or name_related:
                            confidence = "high" if query_in_domain else "medium"
                            
                            company_data = {
                                "name": company_name,
                                "domain": domain,
                                "source": "linkedin",
                                "confidence": confidence
                            }
                            
                            # Add to results - prioritize domain matches
                            if query_in_domain:
                                # Add to beginning of the list for domain matches
                                companies.insert(0, company_data)
                            else:
                                companies.append(company_data)
                            
                            company_names.add(company_name.lower())
                            
                            # Limit results
                            if len(companies) >= 3:
                                break
                    except Exception as e:
                        print(f"Error parsing LinkedIn URL {url_text}: {str(e)}")
                        continue
            
            return companies
        
        except Exception as e:
            print(f"LinkedIn search error: {str(e)}")
            return []
    
    def _extract_domain_from_text(self, text):
        """Try to extract a domain name from text"""
        # Look for common domain patterns
        domain_pattern = r'(?:https?://)?(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]*\.[-a-zA-Z0-9.]+)'
        matches = re.findall(domain_pattern, text)
        
        for match in matches:
            # Filter out common non-company domains
            if not any(match.endswith(suffix) for suffix in [
                '.edu', '.gov', '.org', '.int', '.mil', '.example.com', 
                'wikipedia.org', 'google.com'
            ]):
                return match
                
        return None
    
    def _extract_domain(self, company_name):
        """Extract a potential domain from company name"""
        # Remove common terms that wouldn't be in a domain
        name = company_name.lower()
        for term in [" inc", " inc.", " incorporation", " incorporated", " corporation", " corp", 
                   " corp.", " llc", " co", " co.", " company", " ltd", " ltd.", " limited", 
                   " group", " holdings", " worldwide", " global"]:
            name = name.replace(term, "")
        
        # Replace spaces with nothing and remove special characters
        domain = ''.join(c for c in name if c.isalnum() or c == ' ')
        domain = domain.replace(" ", "")
        
        return f"{domain}.com"
    
    def get_company_logo(self, domain, company_name, upload_folder="app/static/uploads/logos"):
        """
        Get company logo using Clearbit Logo API
        This service provides free company logo lookup by domain
        """
        if not domain:
            return None
        
        # Clearbit Logo API (free, no authentication required)
        logo_url = f"https://logo.clearbit.com/{domain}"
        
        try:
            response = requests.get(logo_url)
            
            # If logo not found, try a fallback
            if response.status_code != 200:
                # Try Wikipedia for logo
                wiki_logo = self._get_wikipedia_logo(company_name)
                if wiki_logo:
                    return wiki_logo
                    
                # Last resort: use UI Avatars to generate a logo based on company name
                # Create an avatar with initials from the company name
                initials = ''.join([word[0].upper() for word in company_name.split() if word])
                if len(initials) > 3:
                    initials = initials[:3]  # Limit to 3 characters max
                elif not initials:
                    initials = company_name[:2].upper()  # Use first two chars if no initials
                
                # Generate a consistent color based on the company name
                # Using hex color instead of HSL for better compatibility with the UI Avatars API
                import hashlib
                
                # Generate a seed from the company name
                hash_object = hashlib.md5(company_name.encode())
                hash_hex = hash_object.hexdigest()
                
                # Use the hash to generate a consistent color in hex format
                r = int(hash_hex[0:2], 16) % 200 + 55  # 55-255 for better contrast
                g = int(hash_hex[2:4], 16) % 200 + 55
                b = int(hash_hex[4:6], 16) % 200 + 55
                background_color = f"{r:02x}{g:02x}{b:02x}"
                
                # Format properly for UI Avatars
                avatar_url = f"https://ui-avatars.com/api/?name={quote(initials)}&background={background_color}&color=fff&bold=true&size=512&format=png"
                
                return avatar_url
            
            # Save the logo locally
            timestamp = int(time.time())
            filename = f"logo_{timestamp}_{secure_filename(domain)}.png"
            
            # Ensure upload directory exists
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            file_path = os.path.join(upload_folder, filename)
            
            with open(file_path, "wb") as f:
                f.write(response.content)
            
            return filename
        
        except Exception as e:
            print(f"Logo retrieval error: {str(e)}")
            return None
            
    def _get_wikipedia_logo(self, company_name):
        """Try to get a company logo from Wikipedia"""
        try:
            # First get the page info for the company
            search_url = "https://en.wikipedia.org/w/api.php"
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": company_name,
                "srnamespace": 0,
                "srlimit": 1
            }
            
            search_response = requests.get(search_url, params=search_params)
            if search_response.status_code != 200 or 'query' not in search_response.json():
                return None
                
            search_data = search_response.json()
            if not search_data['query']['search']:
                return None
                
            title = search_data['query']['search'][0]['title']
            
            # Now get the page images
            image_url = "https://en.wikipedia.org/w/api.php"
            image_params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "images",
                "imlimit": 10
            }
            
            image_response = requests.get(image_url, params=image_params)
            if image_response.status_code != 200:
                return None
                
            image_data = image_response.json()
            pages = image_data.get('query', {}).get('pages', {})
            
            # Find the first logo image
            logo_file = None
            for page_id, page_info in pages.items():
                if 'images' not in page_info:
                    continue
                    
                for image in page_info['images']:
                    image_name = image['title']
                    # Look more specifically for company logo patterns and avoid commons/wikimedia logos
                    if (any(term in image_name.lower() for term in ['logo', 'icon', 'symbol']) and 
                        not any(term in image_name.lower() for term in ['commons', 'wikimedia', 'wiki', 'license'])):
                        logo_file = image_name
                        break
                        
                if logo_file:
                    break
                    
            if not logo_file:
                return None
                
            # Get the image URL
            file_url = "https://en.wikipedia.org/w/api.php"
            file_params = {
                "action": "query",
                "format": "json",
                "titles": logo_file,
                "prop": "imageinfo",
                "iiprop": "url|mime"
            }
            
            file_response = requests.get(file_url, params=file_params)
            if file_response.status_code != 200:
                return None
                
            file_data = file_response.json()
            pages = file_data.get('query', {}).get('pages', {})
            
            # Extract the URL and verify it's an image type
            image_url = None
            mime_type = None
            for page_id, page_info in pages.items():
                if 'imageinfo' in page_info:
                    image_info = page_info['imageinfo'][0]
                    image_url = image_info['url']
                    if 'mime' in image_info:
                        mime_type = image_info['mime']
                    break
                    
            if not image_url:
                return None
                
            # Verify it's an actual image file
            if not mime_type or not mime_type.startswith('image/'):
                print(f"Rejected non-image MIME type: {mime_type}")
                return None
                
            # Avoid SVG images as they may not display correctly
            if mime_type == 'image/svg+xml':
                print(f"Skipping SVG image: {image_url}")
                return None
                
            # Download and save the image
            img_response = requests.get(image_url, stream=True)
            if img_response.status_code != 200:
                return None
                
            # Check file size - if too small, likely not a useful logo
            if int(img_response.headers.get('Content-Length', 0)) < 1000:
                print(f"Image too small, might be a placeholder: {image_url}")
                return None
                
            # Save locally
            timestamp = int(time.time())
            safe_name = secure_filename(company_name) 
            filename = f"logo_wiki_{timestamp}_{safe_name}.png"
            
            upload_folder = "app/static/uploads/logos"
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
                
            file_path = os.path.join(upload_folder, filename)
            
            with open(file_path, "wb") as f:
                f.write(img_response.content)
                
            return filename
            
        except Exception as e:
            print(f"Wikipedia logo retrieval error: {str(e)}")
            return None
    
    def _search_domain_matches(self, query):
        """
        Search for companies where the query string is contained in their domain name
        (e.g., "palant" would match "palantir.com")
        """
        if not query or len(query.strip()) < 3:  # Require at least 3 chars to avoid too many false positives
            return []
            
        query_lower = query.lower()
        
        # List of common TLDs to try 
        common_tlds = ['com', 'co', 'io', 'net', 'org', 'ai', 'tech']
        
        # Try direct domain completion with common TLDs
        potential_domains = []
        for tld in common_tlds:
            potential_domains.append(f"{query_lower}.{tld}")
        
        # Check if these domains resolve (very basic validation)
        valid_companies = []
        
        for domain in potential_domains[:5]:  # Limit to first 5 to avoid excessive checking
            try:
                # Try to get the domain logo via Clearbit as a validation
                logo_url = f"https://logo.clearbit.com/{domain}"
                response = requests.head(logo_url, timeout=2)
                
                if response.status_code == 200:
                    # If we get a valid response, this is likely a real company
                    name_parts = domain.split('.')[0].split('-')
                    name = ' '.join([part.capitalize() for part in name_parts])
                    
                    valid_companies.append({
                        "name": name,
                        "domain": domain,
                        "confidence": "high"  # Clearbit validated
                    })
                    
                    if len(valid_companies) >= 2:  # Limit to 2 direct domain matches
                        break
            except Exception:
                # Skip any errors
                continue
                
        # If we found valid direct domain matches, return them
        if valid_companies:
            return valid_companies
            
        # Try domain-based searching in a broader way
        try:
            # Try a simple search via DuckDuckGo for the domain
            ddg_url = "https://duckduckgo.com/html/"
            
            # Use specific search operators to improve accuracy
            search_query = f'"{query_lower}" company'
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            
            params = {
                "q": search_query
            }
            
            response = requests.get(ddg_url, headers=headers, params=params, timeout=3)
            
            if response.status_code == 200:
                # Extract URLs from the search results
                soup = BeautifulSoup(response.text, 'html.parser')
                result_links = soup.select('.result__url')
                
                companies = []
                seen_domains = set()
                
                for link in result_links[:10]:  # Check first 10 results
                    url_text = link.get_text().lower()
                    
                    # Skip common non-company sites
                    if any(site in url_text for site in ['wikipedia', 'linkedin', 'facebook', 'twitter', 'youtube', 'github']):
                        continue
                        
                    # Look for the query string in the domain
                    if query_lower in url_text:
                        # Extract domain from the URL
                        domain_match = re.search(r'(?:https?://)?(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]*\.[-a-zA-Z0-9.]+)', url_text)
                        if domain_match:
                            domain = domain_match.group(1)
                            
                            # Skip if we've already seen this domain
                            if domain in seen_domains:
                                continue
                                
                            # Skip common non-company domains
                            if any(domain.endswith(suffix) for suffix in ['.edu', '.gov', '.mil', '.example.com']):
                                continue
                                
                            # Generate a name from the domain
                            name_parts = domain.split('.')[0].split('-')
                            name = ' '.join([part.capitalize() for part in name_parts])
                            
                            companies.append({
                                "name": name,
                                "domain": domain
                            })
                            
                            seen_domains.add(domain)
                            
                            # Limit to 3 domain matches
                            if len(companies) >= 3:
                                break
                
                return companies
                
        except Exception as e:
            print(f"Domain search error: {str(e)}")
            return []
            
        return [] 