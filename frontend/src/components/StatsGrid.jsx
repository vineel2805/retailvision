import React from 'react';
import { ArrowDownRight, ArrowUpRight, Users, Zap, Cpu, HardDrive } from 'lucide-react';

export default function StatsGrid({ telemetry }) {
  const cards = [
    {
      title: "Today's Entries",
      value: telemetry?.entries ?? 0,
      icon: ArrowDownRight,
      color: '#10B981',
      bgGlow: 'rgba(16, 185, 129, 0.15)',
    },
    {
      title: "Today's Exits",
      value: telemetry?.exits ?? 0,
      icon: ArrowUpRight,
      color: '#F59E0B',
      bgGlow: 'rgba(245, 158, 11, 0.15)',
    },
    {
      title: 'Current Occupancy',
      value: telemetry?.occupancy ?? 0,
      icon: Users,
      color: '#3B82F6',
      bgGlow: 'rgba(59, 130, 246, 0.15)',
    },
    {
      title: 'Inference FPS',
      value: `${telemetry?.fps ?? 0} FPS`,
      icon: Zap,
      color: '#8B5CF6',
      bgGlow: 'rgba(139, 92, 246, 0.15)',
    },
    {
      title: 'CPU Usage',
      value: `${telemetry?.cpu_usage ?? 0}%`,
      icon: Cpu,
      color: '#06B6D4',
      bgGlow: 'rgba(6, 182, 212, 0.15)',
    },
    {
      title: 'RAM Usage',
      value: `${telemetry?.ram_usage ?? 0}%`,
      icon: HardDrive,
      color: '#EC4899',
      bgGlow: 'rgba(236, 72, 153, 0.15)',
    },
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '16px', margin: '0 24px 24px 24px' }}>
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div key={idx} className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.85rem', color: '#94A3B8', fontWeight: 500 }}>{card.title}</span>
              <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: card.bgGlow, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Icon size={20} color={card.color} />
              </div>
            </div>
            <span style={{ fontSize: '1.8rem', fontWeight: 700, color: card.color }}>
              {card.value}
            </span>
          </div>
        );
      })}
    </div>
  );
}
