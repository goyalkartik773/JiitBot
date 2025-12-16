"""
JIIT Information Hub
====================

Comprehensive social media aggregator for JIIT (Jaypee Institute of Information Technology).
Displays embedded content from all official JIIT social media platforms in one place.

Features:
---------
- Embedded YouTube videos (campus tours, reviews, student experiences)
- Instagram feed integration
- Facebook page feed
- Twitter timeline
- LinkedIn profile
- Reddit discussion summaries
- Direct links to all platforms

Platforms Covered:
------------------
- YouTube: @JIITOfficial
- Instagram: @jiit.official
- Facebook: /jiitofficial
- Twitter: @JaypeeUniversi2
- LinkedIn: Jaypee Institute of Information Technology
- Reddit: Various subreddits (r/Indian_Academia, r/JEENEETards)

Author: Kartik, Manav, Sujal
Supervisor: Dr. Tribhuvan Kumar Tewary
"""

import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
import json

# Note: Page configuration is handled by app.py to avoid conflicts
# st.set_page_config can only be called once per session

st.markdown("""
<style>
    .platform-section {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid;
    }
    .youtube-section { border-left-color: #FF0000; }
    .instagram-section { border-left-color: #E4405F; }
    .facebook-section { border-left-color: #1877F2; }
    .reddit-section { border-left-color: #FF5700; }
    .linkedin-section { border-left-color: #0A66C2; }
    .twitter-section { border-left-color: #1DA1F2; }
    
    .account-card {
        background: #f8f9fa;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        transition: transform 0.2s;
    }
    .account-card:hover {
        transform: translateY(-2px);
    }
    .embed-container {
        position: relative;
        padding-bottom: 56.25%;
        height: 0;
        overflow: hidden;
        max-width: 100%;
        margin: 1.5rem 0;
        background: #000;
        border-radius: 10px;
    }
    .embed-container iframe {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border: 0;
    }
    .category-badge {
        background: #e9ecef;
        color: #495057;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin: 0.2rem;
        display: inline-block;
    }
    .social-embed {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background: white;
    }
    .info-box {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .video-highlight {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin: 1.5rem 0;
        text-align: center;
    }
    .reddit-discussion {
        background: #f8f9fa;
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 10px;
        border-left: 4px solid #FF5700;
    }
    .reddit-discussion h5 {
        color: #FF5700;
        margin-bottom: 1rem;
    }
    .reddit-discussion ul {
        padding-left: 1.5rem;
    }
    .reddit-discussion li {
        margin-bottom: 0.8rem;
        line-height: 1.5;
    }
    .reddit-discussion a {
        color: #007bff;
        text-decoration: none;
    }
    .reddit-discussion a:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)

class JIITContentFetcher:
    """
    Fetches and manages JIIT-related content from various sources.
    
    This class provides methods to retrieve curated content about JIIT,
    including YouTube videos, social media links, and other resources.
    
    Attributes:
        headers (dict): HTTP headers for web requests
    """
    def __init__(self):
        """Initialize the content fetcher with appropriate HTTP headers."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_youtube_videos(self):
        """
        Returns a curated list of JIIT-related YouTube videos.
        
        Returns:
            list: List of dicts containing video information:
                - id: YouTube video ID
                - title: Video title
                - category: Content category (Campus Tour, Overview, etc.)
                - description: Brief description of the video content
        """
        jiit_videos = [
            {
                'id': 'g3fjJBDrN68',
                'title': 'JIIT Noida Campus Tour - Official Campus Walkthrough',
                'category': 'Campus Tour',
                'description': 'Complete campus tour of Jaypee Institute of Information Technology, Noida. See classrooms, labs, hostels, and facilities.'
            },
            {
                'id': 'GNsM3I9SNAA',
                'title': 'JIIT Noida - Complete Overview and Review',
                'category': 'Overview',
                'description': 'Comprehensive overview of JIIT Noida including academics, placements, campus life, and facilities'
            },
            {
                'id': '5Ol0ZhunTEc',
                'title': 'JIIT Noida - Campus Life and Placements',
                'category': 'Campus Life',
                'description': 'Detailed information about campus life, student activities, and placement opportunities at JIIT Noida'
            },
            {
                'id': 'wOjdhq-wg5w',
                'title': 'Life at JIIT Noida - Student Experience',
                'category': 'Student Life',
                'description': 'Real student experiences and daily life at JIIT Noida from current students'
            }
        ]
        return jiit_videos

def extract_video_id(youtube_url):
    """
    Extracts the video ID from various YouTube URL formats.
    
    Supports:
    - Short URLs (youtu.be/VIDEO_ID)
    - Full URLs (youtube.com/watch?v=VIDEO_ID)
    - Direct video IDs
    
    Args:
        youtube_url (str): YouTube URL or video ID
    
    Returns:
        str: Extracted video ID
    """
    # Handle both full URLs and direct IDs
    if 'youtu.be' in youtube_url:
        return youtube_url.split('/')[-1].split('?')[0]
    elif 'youtube.com' in youtube_url:
        return youtube_url.split('v=')[1].split('&')[0]
    else:
        return youtube_url  # Assume it's already a video ID

def embed_youtube_video(video_id, title, description):
    """
    Embeds a YouTube video in the Streamlit app with title and description.
    
    Args:
        video_id (str): YouTube video ID or full URL
        title (str): Video title to display
        description (str): Video description to display
    
    Creates an embedded iframe with responsive sizing.
    """
    # Clean the video ID in case full URL was provided
    clean_video_id = extract_video_id(video_id)
    
    st.markdown(f"#### 🎥 {title}")
    st.markdown(f"*{description}*")
    
    embed_url = f"https://www.youtube.com/embed/{clean_video_id}"
    st.markdown(f"""
    <div class="embed-container">
        <iframe src="{embed_url}" 
                frameborder="0" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
        </iframe>
    </div>
    """, unsafe_allow_html=True)

def embed_instagram_feed():
    """Embed Instagram feed"""
    st.markdown("""
    <div class="social-embed">
        <h4>📸 JIIT Instagram Feed</h4>
        <!-- Instagram feed widget -->
        <iframe src="https://www.instagram.com/jiit.official/embed/" 
                width="100%" 
                height="600" 
                style="border:none;border-radius:10px;" 
                scrolling="no" 
                frameborder="0">
        </iframe>
    </div>
    """, unsafe_allow_html=True)

def embed_facebook_feed():
    """Embed Facebook feed"""
    st.markdown("""
    <div class="social-embed">
        <h4>📘 JIIT Facebook Feed</h4>
        <iframe src="https://www.facebook.com/plugins/page.php?href=https%3A%2F%2Fwww.facebook.com%2Fjiitofficial%2F&tabs=timeline&width=500&height=600&small_header=false&adapt_container_width=true&hide_cover=false&show_facepile=true&appId" 
                width="100%" 
                height="600" 
                style="border:none;overflow:hidden;border-radius:10px;" 
                scrolling="no" 
                frameborder="0" 
                allowfullscreen="true" 
                allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share">
        </iframe>
    </div>
    """, unsafe_allow_html=True)

def embed_twitter_feed():
    """Embed Twitter feed"""
    st.markdown("""
    <div class="social-embed">
        <h4>🐦 JIIT Twitter Feed</h4>
        <a class="twitter-timeline" 
           data-height="600" 
           data-theme="light" 
           href="https://twitter.com/JaypeeUniversi2?ref_src=twsrc%5Etfw">
           Tweets by JaypeeUniversi2
        </a>
        <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
    </div>
    """, unsafe_allow_html=True)

def embed_linkedin_profile():
    """Embed LinkedIn profile"""
    st.markdown("""
    <div class="social-embed">
        <h4>💼 JIIT LinkedIn</h4>
        <div style="display: flex; justify-content: center;">
            <div class="badge-base LI-profile-badge" 
                 data-locale="en_US" 
                 data-size="large" 
                 data-theme="light" 
                 data-type="VERTICAL" 
                 data-vanity="jaypee-institute-of-information-technology" 
                 data-version="v1">
                 <a class="badge-base__link LI-simple-link" 
                    href="https://in.linkedin.com/school/jaypee-institute-of-information-technology/?trk=public_profile_school-profile-section-result-card_subtitle-click">
                 </a>
            </div>
        </div>
        <script src="https://platform.linkedin.com/badges/js/profile.js" async defer type="text/javascript"></script>
    </div>
    """, unsafe_allow_html=True)

def embed_reddit_discussions():
    """Embed Reddit discussions"""
    st.markdown("""
    <div class="reddit-discussion">
        <h5>🤖 Popular JIIT Discussion Threads:</h5>
        <ul>
            <li><strong>JIIT Noida Complete Review</strong> - Comprehensive reviews about JIIT Noida from students and alumni</li>
            <li><strong>JIIT Placements 2023</strong> - Latest placement statistics and company information</li>
            <li><strong>JIIT vs Other Private Colleges</strong> - Comparison with other engineering colleges</li>
            <li><strong>Campus Life at JIIT</strong> - Discussions about hostel life, events, and student activities</li>
        </ul>
        <p><em>Visit r/Indian_Academia and r/JEENEETards for more discussions about JIIT</em></p>
    </div>
    """, unsafe_allow_html=True)

def main():
    """
    Main function that renders the JIIT Information Hub page.
    
    Displays:
    - Page title and description
    - YouTube videos section with featured campus tour
    - Instagram feed with account information
    - Facebook page feed
    - Twitter timeline
    - LinkedIn profile
    - Reddit discussions summary
    - Quick links to all platforms
    
    Each social media platform is displayed in a styled section
    with embedded content and relevant information.
    """
    st.title("🏫 JIIT - All Social Media Content")
    st.markdown("### Watch videos and view posts directly on this page - No external links needed!")
    
    # Initialize content fetcher
    fetcher = JIITContentFetcher()
    
    # YouTube Section
    st.markdown('<div class="platform-section youtube-section">', unsafe_allow_html=True)
    st.markdown("## 🎬 YouTube Videos")
    st.markdown("*Official JIIT videos - Watch directly below*")
    
    # Highlight the campus tour video
    st.markdown("""
    <div class="video-highlight">
        <h3>🚀 Featured Video: Campus Tour</h3>
        <p>Get a complete virtual tour of JIIT Noida campus with this detailed walkthrough</p>
    </div>
    """, unsafe_allow_html=True)
    
    videos = fetcher.get_youtube_videos()
    
    # Display the campus tour video prominently first
    campus_tour_video = videos[0]  # This is your campus tour
    embed_youtube_video(campus_tour_video['id'], campus_tour_video['title'], campus_tour_video['description'])
    
    st.markdown("---")
    st.markdown("### More JIIT Videos")
    
    # Display remaining videos in columns
    cols = st.columns(2)
    for i, video in enumerate(videos[1:], 1):  # Skip first video (campus tour)
        with cols[(i-1) % 2]:
            embed_youtube_video(video['id'], video['title'], video['description'])
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Instagram Section
    st.markdown('<div class="platform-section instagram-section">', unsafe_allow_html=True)
    st.markdown("## 📸 Instagram")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        embed_instagram_feed()
    with col2:
        st.markdown("""
        <div class="info-box">
        ### About JIIT Instagram
        
        **Handle:** @jiit.official  
        **Followers:** 4,900+  
        **Posts:** 1,055+
        
        **Content Includes:**
        - Campus photographs
        - Event highlights
        - Student achievements
        - Daily campus updates
        - Festival celebrations
        - Technical events
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Facebook Section
    st.markdown('<div class="platform-section facebook-section">', unsafe_allow_html=True)
    st.markdown("## 📘 Facebook")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        embed_facebook_feed()
    with col2:
        st.markdown("""
        <div class="info-box">
        ### About JIIT Facebook
        
        **Page:** /jiitofficial  
        **Likes:** 26,800+  
        
        **Content Includes:**
        - Official announcements
        - Event updates
        - News and achievements
        - Community engagement
        - Admission notices
        - Placement updates
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Twitter Section
    st.markdown('<div class="platform-section twitter-section">', unsafe_allow_html=True)
    st.markdown("## 🐦 Twitter")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        embed_twitter_feed()
    with col2:
        st.markdown("""
        <div class="info-box">
        ### About JIIT Twitter
        
        **Handle:** @JaypeeUniversi2  
        
        **Content Includes:**
        - Quick updates and announcements
        - Event live tweets
        - News sharing
        - Community interaction
        - Important deadlines
        - Achievement highlights
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # LinkedIn Section
    st.markdown('<div class="platform-section linkedin-section">', unsafe_allow_html=True)
    st.markdown("## 💼 LinkedIn")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        embed_linkedin_profile()
    with col2:
        st.markdown("""
        <div class="info-box">
        ### About JIIT LinkedIn
        
        **Followers:** 90,000+  
        
        **Content Includes:**
        - Professional networking
        - Job opportunities
        - Alumni success stories
        - Industry partnerships
        - Research publications
        - Corporate relations
        - Placement announcements
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Reddit Section
    st.markdown('<div class="platform-section reddit-section">', unsafe_allow_html=True)
    st.markdown("## 🤖 Reddit Discussions")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        embed_reddit_discussions()
    with col2:
        st.markdown("""
        <div class="info-box">
        ### About JIIT on Reddit
        
        **Popular Subreddits:**
        - r/Indian_Academia
        - r/JEENEETards
        - r/Engineering
        - r/IndiaSpeaks
        
        **Discussion Topics:**
        - Admissions and cutoffs
        - Placement statistics
        - Campus life reviews
        - Hostel facilities
        - Faculty reviews
        - Branch comparisons
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Quick Links Section
    st.markdown("---")
    st.markdown("## 🔗 Quick Links to JIIT Social Media")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        ### 🎬 YouTube
        [Visit YouTube Channel](https://www.youtube.com/@JIITOfficial)
        """)
    
    with col2:
        st.markdown("""
        ### 📸 Instagram
        [Follow on Instagram](https://www.instagram.com/jiit.official/)
        """)
    
    with col3:
        st.markdown("""
        ### 📘 Facebook
        [Like on Facebook](https://www.facebook.com/jiitofficial)
        """)
    
    with col4:
        st.markdown("""
        ### 🐦 Twitter
        [Follow on Twitter](https://twitter.com/JaypeeUniversi2)
        """)
    
    st.markdown("---")
    st.success("✅ **Featured: Official JIIT Campus Tour Video - Watch it above!**")
    st.info("💡 **Tip:** All social media feeds are embedded directly on this page. The campus tour video is featured at the top!")

def show():
    """Function called by app.py to display the JIIT info page"""
    main()

if __name__ == "__main__":
    main()