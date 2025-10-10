"use client"

import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { PanelLeft } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

type SidebarContextType = {
  isCollapsed: boolean
  toggleSidebar: () => void
}

const SidebarContext = React.createContext<SidebarContextType | undefined>(undefined)

export function useSidebar() {
  const context = React.useContext(SidebarContext)
  if (context === undefined) {
    throw new Error("useSidebar must be used within a SidebarProvider")
  }
  return context
}

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [isCollapsed, setIsCollapsed] = React.useState(false)

  const toggleSidebar = () => {
    setIsCollapsed(prev => !prev)
  }

  return (
    <SidebarContext.Provider value={{ isCollapsed, toggleSidebar }}>
      <TooltipProvider delayDuration={0}>
        {children}
      </TooltipProvider>
    </SidebarContext.Provider>
  )
}

export const Sidebar = React.forwardRef<
  HTMLElement,
  React.HTMLAttributes<HTMLElement>
>(({ className, ...props }, ref) => {
  const { isCollapsed } = useSidebar()
  return (
    <aside
      ref={ref}
      data-collapsed={isCollapsed}
      className={cn(
        "fixed left-0 top-0 z-20 flex h-full flex-col border-r bg-background transition-all duration-300 ease-in-out",
        "data-[collapsed=false]:w-60 data-[collapsed=true]:w-[72px]",
        className
      )}
      {...props}
    />
  )
})
Sidebar.displayName = "Sidebar"

export const SidebarHeader = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex h-14 items-center border-b p-4", className)}
    {...props}
  />
))
SidebarHeader.displayName = "SidebarHeader"

export const SidebarContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-1 flex-col overflow-y-auto", className)}
    {...props}
  />
))
SidebarContent.displayName = "SidebarContent"


export const SidebarFooter = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("mt-auto flex flex-col items-center gap-2 border-t p-4", className)}
    {...props}
  />
))
SidebarFooter.displayName = "SidebarFooter"


export const SidebarMenu = React.forwardRef<
  HTMLUListElement,
  React.HTMLAttributes<HTMLUListElement>
>(({ className, ...props }, ref) => (
  <ul
    ref={ref}
    className={cn("flex flex-col gap-1 p-2", className)}
    {...props}
  />
))
SidebarMenu.displayName = "SidebarMenu"


export const SidebarMenuItem = React.forwardRef<
  HTMLLIElement,
  React.HTMLAttributes<HTMLLIElement>
>(({ className, ...props }, ref) => (
  <li
    ref={ref}
    className={cn("group/menu-item relative", className)}
    {...props}
  />
))
SidebarMenuItem.displayName = "SidebarMenuItem"


const sidebarMenuButtonVariants = cva(
  "flex w-full items-center gap-3 rounded-md p-2 text-left text-sm outline-none ring-primary transition-colors focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "text-muted-foreground hover:bg-accent hover:text-accent-foreground data-[active=true]:bg-accent data-[active=true]:text-accent-foreground",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export const SidebarMenuButton = React.memo(
  React.forwardRef<
    HTMLButtonElement,
    React.ComponentProps<"button"> &
      VariantProps<typeof sidebarMenuButtonVariants> & {
        asChild?: boolean
        isActive?: boolean
        tooltip?: React.ReactNode
      }
  >(
    (
      { asChild = false, variant, isActive, tooltip, className, children, ...props },
      ref
    ) => {
      const { isCollapsed } = useSidebar()
      const Comp = asChild ? Slot : "button"

      const button = (
         <Comp
          ref={ref}
          data-active={isActive}
          className={cn(
            sidebarMenuButtonVariants({ variant, className }),
            isCollapsed ? "justify-center" : "justify-start"
          )}
          {...props}
        >
          {children}
        </Comp>
      );
      

      if (tooltip && isCollapsed) {
        return (
          <Tooltip>
            <TooltipTrigger asChild>{button}</TooltipTrigger>
            <TooltipContent side="right" sideOffset={8}>
              {tooltip}
            </TooltipContent>
          </Tooltip>
        )
      }

      return button
    }
  )
)
SidebarMenuButton.displayName = "SidebarMenuButton"

export const SidebarTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ComponentProps<typeof Button>
>(({ className, ...props }, ref) => {
  const { toggleSidebar } = useSidebar()
  return (
    <Button
      ref={ref}
      variant="ghost"
      size="icon"
      className={cn("h-9 w-9", className)}
      onClick={toggleSidebar}
      {...props}
    >
      <PanelLeft className="h-5 w-5" />
      <span className="sr-only">Toggle Sidebar</span>
    </Button>
  )
})
SidebarTrigger.displayName = "SidebarTrigger"

export const SidebarInset = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
    const { isCollapsed } = useSidebar();
    return (
        <main
            ref={ref}
            data-collapsed={isCollapsed}
            className={cn(
                "flex-1 transition-[margin-left] duration-300 ease-in-out",
                "data-[collapsed=false]:ml-60 data-[collapsed=true]:ml-[72px]",
                className
            )}
            {...props}
        />
    )
})
SidebarInset.displayName = "SidebarInset";
