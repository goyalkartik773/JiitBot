"""
JIIT Assistant - Main Application
==================================
A comprehensive web application for JIIT students and faculty that provides:
- AI-powered chatbot for JIIT-related queries
- Automated PPT/Synopsis generator for projects
- Comprehensive JIIT information hub with social media integration

This is the main entry point that handles navigation and page routing.
"""

import streamlit as st
import ppt_generator
import chatbot
import jiit_info
import time

# Configure Streamlit page settings
st.set_page_config(
    page_title="JIIT Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS STYLING
# ============================================================================

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800;900&display=swap');
    
    * {
        font-family: 'Poppins', sans-serif;
    }
    
    /* ===== ANIMATED GRADIENT BACKGROUND ===== */
    .stApp {
        background: linear-gradient(-45deg, #1a0033, #2d1b4e, #3d2a5f, #4a3d6d, #5a4f7d);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        min-height: 100vh;
        position: relative;
        overflow-x: hidden;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Animated mesh gradient overlay */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: 
            radial-gradient(circle at 20% 50%, rgba(255, 107, 107, 0.2) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(255, 159, 64, 0.2) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(75, 192, 192, 0.15) 0%, transparent 50%),
            radial-gradient(circle at 60% 40%, rgba(255, 206, 84, 0.15) 0%, transparent 50%);
        animation: meshMove 20s ease infinite;
        pointer-events: none;
        z-index: 0;
    }
    
    @keyframes meshMove {
        0%, 100% { transform: translate(0, 0) scale(1); }
        33% { transform: translate(50px, 50px) scale(1.1); }
        66% { transform: translate(-50px, -50px) scale(0.9); }
    }
    
    /* ===== REMOVE STREAMLIT DEFAULT STYLES ===== */
    .main .block-container {
        background: transparent;
        padding-top: 2rem;
        padding-bottom: 2rem;
        z-index: 1;
        position: relative;
    }
    
    /* Hide Streamlit header and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* ===== JAW-DROPPING HEADER ===== */
    .main-header {
        font-size: 5rem;
        font-weight: 900;
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 50%, #4ECDC4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin: 2rem 0;
        position: relative;
        animation: titleGlow 3s ease-in-out infinite alternate;
        text-shadow: 0 0 40px rgba(255, 107, 107, 0.6);
        letter-spacing: -2px;
    }
    
    .main-header::before {
        content: '🎓 JIIT Assistant';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 50%, #4ECDC4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: blur(20px);
        opacity: 0.5;
        z-index: -1;
        animation: titleBlur 3s ease-in-out infinite alternate;
    }
    
    @keyframes titleGlow {
        0% {
            filter: drop-shadow(0 0 20px rgba(255, 107, 107, 0.7));
            transform: scale(1);
        }
        100% {
            filter: drop-shadow(0 0 40px rgba(255, 142, 83, 0.9));
            transform: scale(1.02);
        }
    }
    
    @keyframes titleBlur {
        0% { filter: blur(15px); opacity: 0.3; }
        100% { filter: blur(25px); opacity: 0.6; }
    }
    
    /* ===== GLASSMORPHISM CARDS ===== */
    .feature-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 24px;
        padding: 3rem;
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
        position: relative;
        overflow: hidden;
        min-height: 450px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 
            0 8px 32px 0 rgba(0, 0, 0, 0.37),
            inset 0 1px 0 0 rgba(255, 255, 255, 0.1);
    }
    
    .feature-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(
            45deg,
            transparent 30%,
            rgba(255, 107, 107, 0.15) 50%,
            transparent 70%
        );
        transform: rotate(45deg);
        transition: all 0.8s;
        opacity: 0;
    }
    
    .feature-card:hover::before {
        opacity: 1;
        animation: shine 1.5s ease-in-out;
    }
    
    @keyframes shine {
        0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
        100% { transform: translateX(100%) translateY(100%) rotate(45deg); }
    }
    
    .feature-card:hover {
        transform: translateY(-15px) scale(1.03);
        border-color: rgba(255, 107, 107, 0.6);
            box-shadow: 
            0 20px 60px rgba(255, 107, 107, 0.5),
            0 0 40px rgba(255, 142, 83, 0.4),
            inset 0 1px 0 0 rgba(255, 255, 255, 0.2);
        background: rgba(255, 255, 255, 0.05);
    }
    
    /* ===== 3D ICONS ===== */
    .icon {
        font-size: 5rem;
        margin-bottom: 1.5rem;
        display: inline-block;
        animation: float3D 4s ease-in-out infinite;
        text-align: center;
        width: 100%;
        filter: drop-shadow(0 10px 20px rgba(255, 107, 107, 0.5));
        transition: all 0.5s;
    }
    
    .feature-card:hover .icon {
        animation: iconPulse 0.6s ease-in-out;
        transform: scale(1.2) rotate(5deg);
    }
    
    @keyframes float3D {
        0%, 100% { 
            transform: translateY(0px) rotateX(0deg);
        }
        50% { 
            transform: translateY(-15px) rotateX(10deg);
        }
    }
    
    @keyframes iconPulse {
        0%, 100% { transform: scale(1.2) rotate(5deg); }
        50% { transform: scale(1.3) rotate(-5deg); }
    }
    
    /* ===== CARD TITLES ===== */
    .card-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1.5rem;
        text-align: center;
        letter-spacing: -1px;
        position: relative;
    }
    
    .card-title::after {
        content: '';
        position: absolute;
        bottom: -10px;
        left: 50%;
        transform: translateX(-50%);
        width: 60px;
        height: 3px;
        background: linear-gradient(90deg, #FF6B6B, #FF8E53);
        border-radius: 2px;
        opacity: 0;
        transition: all 0.3s;
    }
    
    .feature-card:hover .card-title::after {
        opacity: 1;
        width: 100px;
    }
    
    /* ===== CARD DESCRIPTION ===== */
    .card-description {
        color: rgba(255, 255, 255, 0.7);
        line-height: 1.8;
        font-size: 1.05rem;
        text-align: center;
        flex: 1;
        display: flex;
        align-items: center;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    /* ===== BUTTONS - NEOMORPHISM + GRADIENT ===== */
    .stButton>button {
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 50%, #4ECDC4 100%);
        color: white;
        border: none;
        border-radius: 16px;
        padding: 14px 32px;
        font-weight: 600;
        font-size: 1.05rem;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
            box-shadow: 
            0 8px 24px rgba(255, 107, 107, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
        position: relative;
        overflow: hidden;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    
    .stButton>button::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        width: 0;
        height: 0;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: translate(-50%, -50%);
        transition: width 0.6s, height 0.6s;
    }
    
    .stButton>button:hover::before {
        width: 300px;
        height: 300px;
    }
    
    .stButton>button:hover {
        transform: translateY(-4px) scale(1.05);
            box-shadow: 
            0 16px 40px rgba(255, 107, 107, 0.7),
            0 0 30px rgba(255, 142, 83, 0.5),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
        background: linear-gradient(135deg, #FF8E53 0%, #FF6B6B 50%, #4ECDC4 100%);
        background-size: 200% 200%;
        animation: gradientMove 2s ease infinite;
    }
    
    .stButton>button:active {
        transform: translateY(-2px) scale(1.02);
    }
    
    @keyframes gradientMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* ===== NAVIGATION BUTTONS ===== */
    .nav-button {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        transition: all 0.3s;
        color: white;
        font-weight: 500;
    }
    
    .nav-button:hover {
        background: rgba(255, 107, 107, 0.4);
        border-color: #FF6B6B;
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
    }
    
    /* ===== FEATURE CARDS CONTAINER ===== */
    .feature-cards-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 2rem;
        margin: 3rem 0;
        padding: 1rem;
    }
    
    /* ===== SUBTITLE ===== */
    .subtitle {
        text-align: center;
        color: rgba(255, 255, 255, 0.8);
        font-size: 1.3rem;
        font-weight: 300;
        margin: 2rem 0 3rem;
        letter-spacing: 1px;
    }
    
    /* ===== FEATURE ICONS SECTION ===== */
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 2rem;
        margin: 4rem 0;
        padding: 2rem;
    }
    
    .feature-item {
        text-align: center;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        transition: all 0.4s;
    }
    
    .feature-item:hover {
        transform: translateY(-10px);
        background: rgba(255, 255, 255, 0.06);
        border-color: rgba(255, 107, 107, 0.6);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .feature-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        display: inline-block;
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0 5px 15px rgba(255, 107, 107, 0.6));
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
    }
    
    .feature-item h4 {
        color: #FF6B6B;
        font-weight: 600;
        margin: 1rem 0 0.5rem;
        font-size: 1.2rem;
    }
    
    .feature-item p {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    /* ===== FOOTER ===== */
    .footer {
        text-align: center;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 5rem;
        padding: 3rem 2rem;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.02);
        backdrop-filter: blur(10px);
        border-radius: 24px 24px 0 0;
    }
    
    .footer p {
        margin: 0.5rem 0;
        font-size: 1.1rem;
    }
    
    .footer .footer-tags {
        margin-top: 1.5rem;
        font-size: 0.95rem;
        color: rgba(255, 255, 255, 0.5);
    }
    
    /* ===== ANIMATIONS ===== */
    .animated-content {
        animation: fadeInUp 0.8s ease-out;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(40px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* ===== CUSTOM SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 12px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #FF6B6B, #FF8E53);
        border-radius: 10px;
        border: 2px solid rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #FF8E53, #4ECDC4);
    }
    
    /* ===== SECTION TITLE ===== */
    .section-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 4rem 0 2rem;
        letter-spacing: -1px;
    }
    
    /* ===== RESPONSIVE DESIGN ===== */
    @media (max-width: 768px) {
        .main-header {
            font-size: 3rem;
        }
        
        .feature-card {
            min-height: 400px;
            padding: 2rem;
        }
        
        .icon {
            font-size: 4rem;
        }
        
        .card-title {
            font-size: 1.5rem;
        }
        
        .feature-cards-container {
            grid-template-columns: 1fr;
        }
    }
    
    /* ===== NAVIGATION BAR ===== */
    .nav-bar {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 2rem 0;
        flex-wrap: wrap;
    }
    
    /* ===== STREAMLIT CHAT OVERRIDES ===== */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    /* ===== INPUT FIELDS ===== */
    .stTextInput>div>div>input {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        color: white;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #FF6B6B;
        box-shadow: 0 0 20px rgba(255, 107, 107, 0.4);
    }
    .made-with-love {
    font-size: 1.25rem;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.9);
}

.love-heart {
    color: #FF6B6B;
    font-size: 1.45rem;
    margin: 0 4px;
    display: inline-block;
    animation: heartbeat 1.5s ease-in-out infinite;
}

.team-names {
    background: linear-gradient(135deg, #FF6B6B, #FF8E53, #4ECDC4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 600;           /* ← Slightly less bold now */
    opacity: 0.8;               /* ← Softer presence */
}

.supervisor {
    color: rgba(255, 255, 255, 0.85);
    font-size: 1.15rem;
    margin-top: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    background: linear-gradient(135deg, #FFD93D, #FF6B6B);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 18px rgba(255, 107, 107, 0.6);
}
    
    /* ===== DIVIDER ===== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.5), transparent);
        margin: 3rem 0;
    }
    
    /* ===== LOADING SPINNER OVERRIDE ===== */
    .stSpinner>div {
        border-color: #FF6B6B #FF6B6B transparent transparent;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# ANIMATED BACKGROUND PARTICLES
# ============================================================================

st.markdown("""
<div id="particles-js" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; pointer-events: none;"></div>
<script src="https://cdn.jsdelivr.net/particles.js/2.0.0/particles.min.js"></script>
<script>
particlesJS('particles-js', {
    particles: {
        number: { value: 100, density: { enable: true, value_area: 800 } },
        color: { value: ["#FF6B6B", "#FF8E53", "#4ECDC4", "#FFD93D"] },
        shape: { type: "circle" },
        opacity: { 
            value: 0.6, 
            random: true,
            animation: {
                enable: true,
                speed: 1,
                opacity_min: 0.3,
                sync: false
            }
        },
        size: { 
            value: 4, 
            random: true,
            animation: {
                enable: true,
                speed: 2,
                size_min: 1,
                sync: false
            }
        },
        line_linked: {
            enable: true,
            distance: 150,
            color: "#FF6B6B",
            opacity: 0.2,
            width: 1.5
        },
        move: {
            enable: true,
            speed: 1.5,
            direction: "none",
            random: true,
            straight: false,
            out_mode: "out",
            bounce: false,
            attract: {
                enable: false,
                rotateX: 600,
                rotateY: 1200
            }
        }
    },
    interactivity: {
        detect_on: "canvas",
        events: {
            onhover: { enable: true, mode: "repulse" },
            onclick: { enable: true, mode: "push" },
            resize: true
        },
        modes: {
            grab: { distance: 140, line_linked: { opacity: 1 } },
            bubble: { distance: 400, size: 40, duration: 2, opacity: 8, speed: 3 },
            repulse: { distance: 200, duration: 0.4 },
            push: { particles_nb: 4 },
            remove: { particles_nb: 2 }
        }
    },
    retina_detect: true
});
</script>
""", unsafe_allow_html=True)

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """
    Main application controller that handles routing and page rendering.
    
    This function:
    - Initializes session state variables for page navigation
    - Renders the main header and subtitle
    - Loads the chatbot sidebar (available on all pages)
    - Routes to appropriate page based on session state
    """
    # Initialize session state variables for tracking current and previous pages
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'prev_page' not in st.session_state:
        st.session_state.prev_page = 'home'
    
    # Display animated header with application title
    st.markdown("""
    <div class="main-header animated-content">🎓 JIIT Assistant</div>
    <p class="subtitle animated-content">Your Comprehensive Assistant for JIIT Projects and Information</p>
    """, unsafe_allow_html=True)
    
    # Render chatbot sidebar on all pages for easy access
    # Wrapped in try-except to prevent app crashes if sidebar fails
    try:
        chatbot.render_sidebar()
    except Exception:
        pass
    
    # Handle smooth page transitions with a small delay
    if st.session_state.page != st.session_state.prev_page:
        st.session_state.prev_page = st.session_state.page
        time.sleep(0.1)

    # Route to appropriate page based on current session state
    if st.session_state.page == 'home':
        show_homepage()
    else:
        show_feature_page()

def show_homepage():
    """
    Renders the main homepage with feature cards and information sections.
    
    Displays:
    - Three main feature cards (PPT Generator, Chatbot, JIIT Info)
    - "Why Choose JIIT Assistant" section with key benefits
    - Footer with team information and credits
    
    Each feature card is interactive and navigates to its respective page on click.
    """
    
    # Feature Cards
    st.markdown('<div class="feature-cards-container animated-content">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='feature-card'>
            <div class='card-content'>
                <div class='icon'>📊</div>
                <div class='card-title'>Create PPT/Synopsis</div>
                <div class='card-description'>
                    Generate professional presentations and project synopses in JIIT format. 
                    Input your project details and get a ready-to-download PPT file instantly.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Open PPT Generator", key="ppt_btn", use_container_width=True):
            st.session_state.page = 'ppt_generator'
            st.rerun()
    
    with col2:
        st.markdown("""
        <div class='feature-card'>
            <div class='card-content'>
                <div class='icon'>🤖</div>
                <div class='card-title'>Chatbot Assistant</div>
                <div class='card-description'>
                    Interactive AI assistant for JIIT-related queries. Get instant answers 
                    about courses, campus life, events, admissions, and more with advanced AI.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("💬 Open Chatbot", key="chatbot_btn", use_container_width=True):
            st.session_state.page = 'chatbot'
            st.rerun()
    
    with col3:
        st.markdown("""
        <div class='feature-card'>
            <div class='card-content'>
                <div class='icon'>🏫</div>
                <div class='card-title'>Everything About JIIT</div>
                <div class='card-description'>
                    Comprehensive information hub about JIIT - campus life, events, 
                    student opinions, facilities, Placements and institutional details all in one place.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔍 Explore JIIT Info", key="info_btn", use_container_width=True):
            st.session_state.page = 'jiit_info'
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Why Choose Section
    st.markdown('<h2 class="section-title animated-content">Why Choose JIIT Assistant?</h2>', unsafe_allow_html=True)
    
    st.markdown('<div class="features-grid animated-content">', unsafe_allow_html=True)
    
    feat_col1, feat_col2, feat_col3, feat_col4 = st.columns(4)
    
    with feat_col1:
        st.markdown("""
        <div class='feature-item'>
            <div class='feature-icon'>⚡</div>
            <h4>Lightning Fast</h4>
            <p>Instant access to information with optimized performance</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col2:
        st.markdown("""
        <div class='feature-item'>
            <div class='feature-icon'>🎯</div>
            <h4>Highly Accurate</h4>
            <p>Reliable JIIT-specific Student Employee Data from official sources</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col3:
        st.markdown("""
        <div class='feature-item'>
            <div class='feature-icon'>🔄</div>
            <h4>Always Updated</h4>
            <p>Real-time updates and dynamic content synchronization</p>
        </div>
        """, unsafe_allow_html=True)
    
    with feat_col4:
        st.markdown("""
        <div class='feature-item'>
            <div class='feature-icon'>💡</div>
            <h4>AI-Powered</h4>
            <p>Smart features powered by advanced AI technology</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div class='footer animated-content'>
        <p style='font-size: 1.3rem; font-weight: 600;'>🎓 JIIT Assistant</p>
        <p>Streamlining your JIIT experience with cutting-edge technology</p>
        <div class='footer-tags'>
            ⚡ Powered by Streamlit • 🤖 AI Enhanced • 🎯 JIIT Focused • ❤️ Built for Community
        </div>
        <div>
         <p class='made-with-love'>
        Made with <span class='love-heart'>❤️</span> by 
        <span class='team-names'>Kartik • Manav • Sujal</span>
        </p>
        <p class='supervisor'>
        Under the supervision of <strong>Dr. Tribhuvan Kumar Tewary</strong>
        </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    


def show_feature_page():
    """
    Renders feature pages with a navigation bar.
    
    Displays:
    - Top navigation bar with buttons for all pages
    - The selected feature page content (PPT Generator, Chatbot, or JIIT Info)
    
    The navigation bar allows quick switching between different features
    without returning to the homepage.
    """
    
    # Navigation Bar
    st.markdown('<div class="nav-bar animated-content">', unsafe_allow_html=True)
    
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1, 1, 1, 1])
    
    with nav_col1:
        if st.button("🏠 Home", use_container_width=True, key="nav_home"):
            st.session_state.page = 'home'
            st.rerun()
    
    with nav_col2:
        if st.button("📊 PPT", use_container_width=True, key="nav_ppt"):
            st.session_state.page = 'ppt_generator'
            st.rerun()
    
    with nav_col3:
        if st.button("🤖 Chat", use_container_width=True, key="nav_chat"):
            st.session_state.page = 'chatbot'
            st.rerun()
    
    with nav_col4:
        if st.button("🏫 Info", use_container_width=True, key="nav_info"):
            st.session_state.page = 'jiit_info'
            st.rerun()
    
    with nav_col5:
        if st.button("🔄 Refresh", use_container_width=True, key="nav_refresh"):
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Display feature pages
    if st.session_state.page == 'ppt_generator':
        ppt_generator.show()
    elif st.session_state.page == 'chatbot':
        chatbot.show()
    elif st.session_state.page == 'jiit_info':
        jiit_info.show()
    
# Enhanced JavaScript for smooth animations
st.markdown("""
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll animations with Intersection Observer
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe all animated elements
    const animatedElements = document.querySelectorAll('.animated-content');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(40px)';
        el.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
        observer.observe(el);
    });
    
    // Enhanced button ripple effect
    const buttons = document.querySelectorAll('.stButton button');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});
</script>

<style>
.ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.6);
    transform: scale(0);
    animation: ripple-animation 0.6s ease-out;
    pointer-events: none;
}

@keyframes ripple-animation {
    to {
        transform: scale(4);
        opacity: 0;
    }
}
</style>
""", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
