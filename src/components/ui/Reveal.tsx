import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

interface RevealProps {
  children: React.ReactNode;
  /** Stagger offset in seconds */
  delay?: number;
  /** Travel distance in px */
  y?: number;
  className?: string;
}

/**
 * Reveal — a 200ms ease-out entrance used across pages.
 * Fully disabled when the user prefers reduced motion.
 */
export const Reveal: React.FC<RevealProps> = ({
  children,
  delay = 0,
  y = 8,
  className = ''
}) => {
  const reduce = useReducedMotion();

  if (reduce) return <div className={className}>{children}</div>;

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-40px' }}
      transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1], delay }}
    >
      {children}
    </motion.div>
  );
};
