import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';

const services = [
  { id: 'walk', title: 'Прогулка с собакой', subtitle: '30/60 минут', description: 'Забираем и возвращаем питомца, фотоотчёт, GPS‑трек.', price: 'от 800 ₽' },
  { id: 'sitting', title: 'Догситтинг', subtitle: 'Дома у вас', description: 'Забота, кормление, игры. Ежедневные отчеты в мессенджер.', price: 'от 1500 ₽/день' },
  { id: 'groom', title: 'Груминг', subtitle: 'Салон/на дому', description: 'Гигиена, уход за шерстью и когтями. Аккуратно и бережно.', price: 'от 2000 ₽' },
  { id: 'vet', title: 'Вет‑консультация', subtitle: 'Онлайн/офлайн', description: 'Первичный осмотр, рекомендации по уходу и питанию.', price: 'от 1200 ₽' },
];

export default function ServicesPage() {
  return (
    <main className="page container">
      <h1>Услуги</h1>
      <div className="services-grid">
        {services.map((s) => (
          <Card key={s.id} title={s.title} subtitle={s.subtitle} actions={<span>{s.price}</span>}>
            <p>{s.description}</p>
            <div style={{ marginTop: 12 }}>
              <Button>Заказать</Button>
              <Button variant="secondary" style={{ marginLeft: 8 }}>Подробнее</Button>
            </div>
          </Card>
        ))}
      </div>
    </main>
  );
}


