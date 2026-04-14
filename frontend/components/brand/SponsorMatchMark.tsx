import Image from "next/image";
import { cn } from "@/lib/utils";

type Props = {
  className?: string;
  /** Nav bar default; sm for inline badges */
  size?: "sm" | "md" | "lg";
  priority?: boolean;
  /** Use empty string next to visible text (badge) */
  alt?: string;
};

const heightClass = {
  sm: "h-6",
  md: "h-9",
  lg: "h-12",
} as const;

/** Served from /public — spaces encoded for reliable loading */
const LOGO_PATH =
  "/Interlocking%20puzzle%20pieces%20logo%20(1).png";

export function SponsorMatchMark({
  className,
  size = "md",
  priority = false,
  alt = "SponsorMatch",
}: Props) {
  return (
    <Image
      src={LOGO_PATH}
      alt={alt}
      width={320}
      height={128}
      priority={priority}
      className={cn(
        "w-auto object-contain object-left",
        heightClass[size],
        className
      )}
    />
  );
}
