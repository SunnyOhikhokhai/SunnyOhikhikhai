import { useQuery } from "@tanstack/react-query";
import { Bell, LayoutDashboard, LogOut, Menu, Search, Settings, Shield, UserRound } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown";
import { useAuth } from "@/hooks/useAuth";
import { getData } from "@/lib/api";
import { NAV_LINKS } from "@/lib/constants";
import { cn, initials } from "@/lib/utils";
import { GlobalSearch } from "./GlobalSearch";

export function NotificationBell({ className }: { className?: string }) {
  const { data } = useQuery({
    queryKey: ["notifications", "unread"],
    queryFn: () => getData<{ unread: number }>("/api/notifications/unread-count"),
    refetchInterval: 60_000,
  });
  const n = data?.unread ?? 0;
  return (
    <Link
      to="/notifications"
      className={cn("relative flex size-10 items-center justify-center rounded-xl text-navy transition hover:bg-navy-50", className)}
      aria-label={n ? `Notifications, ${n} unread` : "Notifications"}
    >
      <Bell className="size-5" />
      {n > 0 && (
        <span className="absolute right-1 top-1 flex min-w-[18px] items-center justify-center rounded-full bg-green-600 px-1 text-[10px] font-bold leading-[18px] text-white ring-2 ring-white">
          {n > 99 ? "99+" : n}
        </span>
      )}
    </Link>
  );
}

function UserMenu() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;
  const doLogout = async () => {
    await logout();
    toast.success("You have been logged out securely.");
    navigate("/");
  };
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 rounded-xl p-1 pr-2 transition hover:bg-navy-50" aria-label="Account menu">
          <span className="flex size-9 items-center justify-center rounded-lg bg-navy text-sm font-bold text-white">{initials(user.full_name)}</span>
          <span className="hidden max-w-[8rem] truncate text-sm font-semibold text-navy xl:block">{user.first_name}</span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>
          <p className="truncate text-sm font-semibold text-navy">{user.full_name}</p>
          <p className="truncate text-xs text-muted-foreground">{user.area_council?.name ?? "No Area Council selected"}</p>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => navigate("/dashboard")}>
          <LayoutDashboard /> Dashboard
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => navigate("/notifications")}>
          <Bell /> Notifications
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => navigate("/settings")}>
          <Settings /> Account settings
        </DropdownMenuItem>
        {user.admin && (
          <DropdownMenuItem onSelect={() => navigate("/admin")}>
            <Shield /> Admin dashboard
          </DropdownMenuItem>
        )}
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={doLogout} className="text-red-600 focus:bg-red-50 focus:text-red-700 [&_svg]:text-red-500">
          <LogOut /> Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function SiteHeader() {
  const { user } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => setMenuOpen(false), [location.pathname]);
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setSearchOpen(true);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const linkCls = ({ isActive }: { isActive: boolean }) =>
    cn(
      "relative rounded-lg px-2.5 py-2 text-[14px] font-semibold transition-colors hover:text-green-600",
      isActive ? "text-navy after:absolute after:inset-x-2.5 after:-bottom-[13px] after:h-[3px] after:rounded-full after:bg-green-500" : "text-slate-600",
    );

  return (
    <>
      <header
        className={cn(
          "sticky top-0 z-40 border-b bg-white/90 backdrop-blur-lg transition-shadow supports-[backdrop-filter]:bg-white/80",
          scrolled ? "border-border shadow-[0_4px_20px_-12px_rgba(6,59,102,0.25)]" : "border-transparent",
        )}
      >
        <div className="container flex h-16 items-center gap-3 lg:h-[72px]">
          <Link to="/" className="mr-2 shrink-0 rounded-lg" aria-label="NIPAM home">
            <Logo />
          </Link>
          <nav aria-label="Main" className="hidden flex-1 items-center justify-center gap-0.5 lg:flex">
            {NAV_LINKS.map((l) => (
              <NavLink key={l.to} to={l.to} end={l.to === "/"} className={linkCls}>
                {l.label}
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-1.5 lg:ml-0">
            <Button variant="ghost" size="icon" onClick={() => setSearchOpen(true)} aria-label="Search (Ctrl+K)">
              <Search className="!size-5" />
            </Button>
            {user ? (
              <>
                <NotificationBell />
                <UserMenu />
              </>
            ) : (
              <div className="hidden items-center gap-2 sm:flex">
                <Button asChild variant="ghost">
                  <Link to="/login">Login</Link>
                </Button>
                <Button asChild>
                  <Link to="/join">Join NIPAM</Link>
                </Button>
              </div>
            )}
            <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setMenuOpen(true)} aria-label="Open menu" aria-expanded={menuOpen}>
              <Menu className="!size-6" />
            </Button>
          </div>
        </div>
      </header>

      <Dialog open={menuOpen} onOpenChange={setMenuOpen}>
        <DialogContent side="right" className="flex flex-col p-0" aria-describedby={undefined}>
          <div className="border-b border-border p-5">
            <DialogTitle className="sr-only">Menu</DialogTitle>
            <Logo variant="with-name" />
          </div>
          <nav aria-label="Mobile" className="flex-1 overflow-y-auto p-3">
            {NAV_LINKS.map((l) => (
              <NavLink
                key={l.to}
                to={l.to}
                end={l.to === "/"}
                className={({ isActive }) =>
                  cn("flex items-center rounded-xl px-4 py-3 text-base font-semibold transition", isActive ? "bg-navy-50 text-navy" : "text-slate-700 hover:bg-surface")
                }
              >
                {l.label}
              </NavLink>
            ))}
            {user && (
              <div className="mt-3 border-t border-border pt-3">
                <NavLink to="/dashboard" className="flex items-center gap-3 rounded-xl px-4 py-3 font-semibold text-slate-700 hover:bg-surface">
                  <LayoutDashboard className="size-5 text-green-600" /> My dashboard
                </NavLink>
                <NavLink to="/settings" className="flex items-center gap-3 rounded-xl px-4 py-3 font-semibold text-slate-700 hover:bg-surface">
                  <UserRound className="size-5 text-green-600" /> Account settings
                </NavLink>
                {user.admin && (
                  <NavLink to="/admin" className="flex items-center gap-3 rounded-xl px-4 py-3 font-semibold text-slate-700 hover:bg-surface">
                    <Shield className="size-5 text-green-600" /> Admin dashboard
                  </NavLink>
                )}
              </div>
            )}
          </nav>
          {!user && (
            <div className="grid gap-2 border-t border-border p-4 pb-safe">
              <Button asChild size="lg">
                <Link to="/join">Join NIPAM</Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link to="/login">Login</Link>
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <GlobalSearch open={searchOpen} onOpenChange={setSearchOpen} />
    </>
  );
}
