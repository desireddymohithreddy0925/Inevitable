import { useEffect, useRef } from 'react';

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  color: string;
  verified: boolean;
  pulseOffset: number;
}

interface EdgePulse {
  fromIndex: number;
  toIndex: number;
  progress: number;
  speed: number;
  color: string;
}

export default function VerificationMeshCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Mouse coordinates
    let mouse = { x: -1000, y: -1000, radius: 180 };

    const handleMouseMove = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('resize', handleResize);

    // Verification theme palette: Deep Azure, Cyber Cyan, Emerald Proof, Quantum Violet
    const colors = ['#3B82F6', '#06B6D4', '#10B981', '#8B5CF6'];

    // Create particles representing AST & Verification nodes
    const particleCount = Math.min(Math.floor((width * height) / 18000), 75);
    const particles: Particle[] = [];

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.45,
        vy: (Math.random() - 0.5) * 0.45,
        radius: Math.random() * 2 + 1.5,
        color: colors[Math.floor(Math.random() * colors.length)],
        verified: Math.random() > 0.6,
        pulseOffset: Math.random() * Math.PI * 2,
      });
    }

    // Packet pulses traveling along edges
    const pulses: EdgePulse[] = [];
    const spawnPulse = () => {
      if (particles.length < 2) return;
      const fromIndex = Math.floor(Math.random() * particles.length);
      // Find a near neighbor
      let toIndex = -1;
      let minDist = 150;
      for (let j = 0; j < particles.length; j++) {
        if (fromIndex === j) continue;
        const dx = particles[fromIndex].x - particles[j].x;
        const dy = particles[fromIndex].y - particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < minDist) {
          toIndex = j;
          break;
        }
      }
      if (toIndex !== -1 && pulses.length < 8) {
        pulses.push({
          fromIndex,
          toIndex,
          progress: 0,
          speed: 0.015 + Math.random() * 0.02,
          color: particles[fromIndex].color,
        });
      }
    };

    let pulseTimer = 0;
    let scanLineY = 0;
    const scanSpeed = 1.2;

    const render = (time: number) => {
      ctx.clearRect(0, 0, width, height);

      // 1. Draw subtle horizontal laser scan line (Security / Code Proof verification scan)
      scanLineY = (scanLineY + scanSpeed) % (height + 200);
      const gradient = ctx.createLinearGradient(0, scanLineY - 80, 0, scanLineY);
      gradient.addColorStop(0, 'rgba(6, 182, 212, 0)');
      gradient.addColorStop(0.5, 'rgba(6, 182, 212, 0.03)');
      gradient.addColorStop(1, 'rgba(16, 185, 129, 0.12)');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, scanLineY - 80, width, 80);

      ctx.strokeStyle = 'rgba(16, 185, 129, 0.35)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, scanLineY);
      ctx.lineTo(width, scanLineY);
      ctx.stroke();

      // Spawn proof execution pulses periodically
      pulseTimer++;
      if (pulseTimer % 45 === 0) {
        spawnPulse();
      }

      // 2. Update and draw nodes
      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];

        // Move
        p.x += p.vx;
        p.y += p.vy;

        // Bounce boundaries
        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;

        // Mouse gravity & interaction
        const mdx = mouse.x - p.x;
        const mdy = mouse.y - p.y;
        const mDist = Math.sqrt(mdx * mdx + mdy * mdy);
        if (mDist < mouse.radius) {
          const force = (1 - mDist / mouse.radius) * 0.8;
          p.x += (mdx / mDist) * force;
          p.y += (mdy / mDist) * force;
        }

        // Scan line intersection triggers instant glowing "verified" effect
        const distToScan = Math.abs(p.y - scanLineY);
        const isScanningNow = distToScan < 30;

        // Draw node
        ctx.beginPath();
        const pulseSize = Math.sin(time * 0.003 + p.pulseOffset) * 0.6;
        ctx.arc(p.x, p.y, p.radius + pulseSize + (isScanningNow ? 2 : 0), 0, Math.PI * 2);

        if (isScanningNow) {
          ctx.fillStyle = '#10B981';
          ctx.shadowColor = '#10B981';
          ctx.shadowBlur = 12;
        } else {
          ctx.fillStyle = p.color;
          ctx.shadowColor = p.color;
          ctx.shadowBlur = p.verified ? 6 : 2;
        }
        ctx.fill();
        ctx.shadowBlur = 0; // reset
      }

      // 3. Connect nodes with proof graph edges
      const maxDistance = 140;
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);

          if (dist < maxDistance) {
            const alpha = (1 - dist / maxDistance) * 0.22;
            ctx.beginPath();
            ctx.strokeStyle = `rgba(59, 130, 246, ${alpha})`;
            ctx.lineWidth = 0.8;
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.stroke();
          }
        }

        // Also draw edge to mouse cursor if within range
        const mdx = mouse.x - particles[i].x;
        const mdy = mouse.y - particles[i].y;
        const mDist = Math.sqrt(mdx * mdx + mdy * mdy);
        if (mDist < mouse.radius) {
          const alpha = (1 - mDist / mouse.radius) * 0.45;
          ctx.beginPath();
          ctx.strokeStyle = `rgba(6, 182, 212, ${alpha})`;
          ctx.lineWidth = 1;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(mouse.x, mouse.y);
          ctx.stroke();
        }
      }

      // 4. Draw moving proof verification pulses along edges
      for (let k = pulses.length - 1; k >= 0; k--) {
        const pulse = pulses[k];
        pulse.progress += pulse.speed;

        if (pulse.progress >= 1) {
          pulses.splice(k, 1);
          continue;
        }

        const from = particles[pulse.fromIndex];
        const to = particles[pulse.toIndex];
        if (!from || !to) continue;

        const px = from.x + (to.x - from.x) * pulse.progress;
        const py = from.y + (to.y - from.y) * pulse.progress;

        ctx.beginPath();
        ctx.arc(px, py, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = '#FFFFFF';
        ctx.shadowColor = pulse.color;
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;
      }

      animationFrameId = requestAnimationFrame(render);
    };

    animationFrameId = requestAnimationFrame(render);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        pointerEvents: 'none',
        zIndex: 1,
        opacity: 0.85,
      }}
    />
  );
}
