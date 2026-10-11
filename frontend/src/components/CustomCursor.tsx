import { useEffect, useState } from 'react';

export default function CustomCursor() {
  const [position, setPosition] = useState({ x: -100, y: -100 });
  const [isHovering, setIsHovering] = useState(false);

  useEffect(() => {
    const updatePosition = (e: MouseEvent) => {
      setPosition({ x: e.clientX, y: e.clientY });
      
      // Check if hovering over clickable element
      const target = e.target as HTMLElement;
      const isClickable = target.closest('a, button, input, textarea, select, .feature-card, .dev-panel, .sidebar-nav li');
      setIsHovering(!!isClickable);
    };
    
    window.addEventListener('mousemove', updatePosition);
    return () => window.removeEventListener('mousemove', updatePosition);
  }, []);

  return (
    <>
      <div 
        className="cursor-glow" 
        style={{ transform: `translate3d(${position.x}px, ${position.y}px, 0)` }}
      />
      <div 
        className={`cursor-glass ${isHovering ? 'hovering' : ''}`} 
        style={{ transform: `translate3d(${position.x}px, ${position.y}px, 0) scale(${isHovering ? 1.5 : 1})` }}
      />
      <div 
        className="cursor-dot" 
        style={{ transform: `translate3d(${position.x}px, ${position.y}px, 0)` }}
      />
    </>
  );
}
