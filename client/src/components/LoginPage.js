import React, { useState } from 'react';
import { supabase } from '../supabaseClient';
import '../styles/LoginPage.css';

const LoginPage = ({ onAboutClick }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isSignUp, setIsSignUp] = useState(true); // Default to signup mode

  const handleSignIn = async (e) => {
    e.preventDefault();
    try {
      setError(null);
      setLoading(true);
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (error) throw error;
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async (e) => {
    e.preventDefault();
    try {
      setError(null);
      setLoading(true);
      const { error } = await supabase.auth.signUp({
        email,
        password,
      });
      if (error) throw error;
      alert('Check your email for the confirmation link!');
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-content">
        <header className="header">
          <div className="logo-container">
            <span className="logo-text">HinduAI</span>
          </div>
          <button className="about-button" onClick={onAboutClick}>About</button>
        </header>

        <div className="auth-form">
          <h2>{isSignUp ? 'Create Account' : 'Sign In'}</h2>
          <form onSubmit={isSignUp ? handleSignUp : handleSignIn}>
            <div className="form-group">
              <input
                type="email"
                placeholder="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <button type="submit" className="submit-button" disabled={loading}>
              {loading ? 'Loading...' : isSignUp ? 'Sign Up' : 'Sign In'}
            </button>
            <button
              type="button"
              className="toggle-auth-button"
              onClick={() => setIsSignUp(!isSignUp)}
            >
              {isSignUp ? 'Already have an account? Sign In' : 'Need an account? Sign Up'}
            </button>
          </form>
        </div>

        <p className="disclaimer">
          HinduAI is an AI assistant and does not replace the guidance of qualified spiritual teachers.
          For questions or feedback, email us at{' '}
          <a href="mailto:hinduai@gmail.com">hinduai@gmail.com</a>
        </p>
      </div>
    </div>
  );
};

export default LoginPage; 