import React from 'react';
import '../styles/AboutPage.css';

const AboutPage = ({ user }) => {
  return (
    <div className="about-container">
      <h1>About Hindu AI</h1>
      <div className="about-content">
        <p>
          <strong>Our mission is to make Hindu spiritual knowledge accessible to everyone, everywhere.</strong>
        </p>
        <p>
          Hindu AI is an intelligent spiritual guide designed to help seekers, students, and curious minds explore the rich traditions, philosophies, and practices of Hinduism. Whether you're beginning your spiritual journey or deepening your understanding, we provide personalized insights and guidance.
        </p>
        <p>
          Hindu AI was created to bridge the gap between ancient wisdom and modern seekers. Drawing from authentic sources and traditions, we offer clear, reliable information about Hindu philosophy, rituals, scriptures, and cultural practices. Our AI companion helps you navigate complex concepts, understand spiritual teachings, and find practical ways to incorporate these insights into your daily life.
        </p>
        <p>
          <strong>Note:</strong> Hindu AI is a spiritual guide and companion, not a replacement for traditional learning or the guidance of qualified spiritual teachers. For specific spiritual matters or personal guidance, please consult with qualified spiritual teachers or scholars.
        </p>
      </div>
      {user ? (
        <button 
          className="back-to-home"
          onClick={() => window.location.reload()}
        >
          Back to Home
        </button>
      ) : (
        <button 
          className="back-to-login"
          onClick={() => window.location.reload()}
        >
          Back to Login
        </button>
      )}
    </div>
  );
};

export default AboutPage; 
