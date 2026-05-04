import Image from "next/image";

export function BrandLogo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <Image src="/LogoVF.png" alt="Victor Figueroa Arquitecto de Soluciones" width={compact ? 190 : 340} height={64} priority className="h-auto w-auto max-w-full" />
    </div>
  );
}
