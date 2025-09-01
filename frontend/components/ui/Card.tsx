import React from 'react';

type CardProps = React.HTMLAttributes<HTMLDivElement> & {
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
  clickable?: boolean;
};

export function Card({ title, subtitle, actions, children, className = '', clickable = false, ...props }: CardProps) {
  return (
    <div
      className={`card ${clickable ? 'card-link' : ''} ${className}`}
      role={clickable ? 'button' : undefined}
      tabIndex={clickable ? 0 : undefined}
      {...props}
    >
      {(title || actions) && (
        <div className="card-header">
          {title && <h3 className="card-title">{title}</h3>}
          {actions && <div className="card-actions">{actions}</div>}
        </div>
      )}
      {subtitle && <p className="card-subtitle">{subtitle}</p>}
      <div className="card-content">{children}</div>
    </div>
  );
}


