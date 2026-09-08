with open('expense_login.css', 'a', encoding='utf-8') as f:
    f.write('''
/* --- Google OAuth Button --- */
.google-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  padding: 12px;
  background: #ffffff;
  color: #334155;
  font-family: 'Inter', sans-serif;
  font-size: 14.5px;
  font-weight: 600;
  border-radius: 12px;
  text-decoration: none;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}
.google-btn:hover {
  background: #f8fafc;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}
.google-btn svg {
  width: 20px;
  height: 20px;
}

/* --- Divider --- */
.divider {
  display: flex;
  align-items: center;
  text-align: center;
  margin-bottom: 20px;
  color: #64748b;
  font-size: 12px;
  font-weight: 500;
}
.divider::before, .divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.divider span {
  padding: 0 12px;
}

/* --- Auth Link --- */
.auth-link {
  text-align: center;
  margin-top: 20px;
  font-size: 13.5px;
  color: var(--text-muted);
}
.auth-link a {
  color: var(--accent);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}
.auth-link a:hover {
  color: var(--accent-hover);
  text-decoration: underline;
}
''')
