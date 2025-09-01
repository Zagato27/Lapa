import './globals.css';
import type { Metadata } from 'next';
import Link from 'next/link';
import { Inter } from 'next/font/google';
import localFont from 'next/font/local';
import { ThemeProvider } from './theme-provider';
import { AuthProvider } from './auth-provider';
import { HeaderAuthControls } from './sections/header-auth-controls';

const inter = Inter({ subsets: ['latin', 'cyrillic'], display: 'swap', variable: '--font-inter' });
const cgBlack = localFont({ src: [{ path: '../public/fonts/CenturyGothicPaneuropeanBlack.ttf', weight: '900', style: 'normal' }], display: 'swap', variable: '--font-fatboy' });
const cgThin = localFont({ src: [{ path: '../public/fonts/CenturyGothicPaneuropeanThin.ttf', weight: '100', style: 'normal' }], display: 'swap', variable: '--font-body' });

export const metadata: Metadata = {
  title: 'Lapa',
  description: 'Lapa Frontend',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" className={`${inter.variable} ${cgBlack.variable} ${cgThin.variable}`}>
      <body>
        <ThemeProvider>
        <AuthProvider>
        <header className="site-header">
          <div className="container site-header-content">
            <Link href="/" className="site-logo" aria-label="На главную">
              <span style={{ fontFamily: 'var(--font-fatboy)', color: 'var(--color-forest)', fontWeight: 900 }}>О! ЛАПА</span>
            </Link>
            <nav className="site-nav" aria-label="Главная навигация">
              <Link href="/" className="nav-link">Главная страница</Link>
              <Link href="/services" className="nav-link">Услуги</Link>
              <Link href="/about" className="nav-link">О нас</Link>
              <Link href="/faq" className="nav-link">FAQ</Link>
            </nav>
            <HeaderAuthControls />
          </div>
        </header>

        {children}

        <footer className="site-footer">
          <div className="container footer-grid">
            <section>
              <h3 className="footer-title">Контакты</h3>
              <p>Email: <a href="mailto:support@lapa.local">support@lapa.local</a></p>
              <p>Телефон: <a href="tel:+79991234567">+7 (999) 123-45-67</a></p>
            </section>
            <section>
              <h3 className="footer-title">Мы в соцсетях</h3>
              <p className="social-links">
                <a href="https://t.me/lapa" target="_blank" rel="noopener noreferrer">Telegram</a>
                <a href="https://vk.com/lapa" target="_blank" rel="noopener noreferrer">VK</a>
                <a href="https://youtube.com/@lapa" target="_blank" rel="noopener noreferrer">YouTube</a>
              </p>
              <p>
                <Link href="/privacy">Политика конфиденциальности</Link>
              </p>
            </section>
          </div>
          <div className="footer-bottom">
            <div className="container">© {new Date().getFullYear()} Lapa. Все права защищены.</div>
          </div>
        </footer>
        </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}


