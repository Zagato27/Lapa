import Link from 'next/link';

export default function HomePage() {
  return (
    <main className="page" style={{ paddingTop: 5 }}>
      <section>
        <div className="container home-hero">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr', alignContent: 'center' }}>
            <h1 className="hero-title" style={{ textAlign: 'left' }}>Ваш надежный сервис для питомцев</h1>
            <p className="hero-subtitle" style={{ textAlign: 'left', maxWidth: 740 }}>
              Прогулки, уход и забота — просто и удобно.
              Единый кабинет, прозрачные заказы, живой трекинг, фотоотчёты и быстрые оплаты.
              Мы подберём проверенного выгульщика и возьмём на себя организацию.
            </p>
            <div style={{ textAlign: 'left' }}>
              <Link href="/services" className="hero-cta">Заказать услугу</Link>
            </div>
          </div>
          <div style={{ justifySelf: 'end' }}>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/images/home/hero.png" alt="ЛаПа баннер" style={{ display: 'block', width: 'min(520px, 40vw)', height: 'auto' }} />
          </div>
        </div>
      </section>
    </main>
  );
}


