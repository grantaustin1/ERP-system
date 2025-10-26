import React from 'react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';
import { Button } from './ui/button';

/**
 * Button with built-in tooltip support
 * Usage:
 * <TooltipButton tooltip="This button adds a new member">
 *   <UserPlus /> Add Member
 * </TooltipButton>
 * 
 * Or with render prop for custom buttons:
 * <TooltipButton tooltip="Delete this item">
 *   {(props) => <IconButton {...props} icon={Trash} />}
 * </TooltipButton>
 */
export default function TooltipButton({ 
  children, 
  tooltip, 
  side = "top",
  disabled = false,
  ...buttonProps 
}) {
  // If no tooltip provided, just render the button
  if (!tooltip) {
    return typeof children === 'function' ? children(buttonProps) : (
      <Button disabled={disabled} {...buttonProps}>
        {children}
      </Button>
    );
  }

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          {typeof children === 'function' ? children(buttonProps) : (
            <Button disabled={disabled} {...buttonProps}>
              {children}
            </Button>
          )}
        </TooltipTrigger>
        <TooltipContent 
          side={side}
          className="bg-slate-900 text-white border-slate-700 max-w-xs"
        >
          <p>{tooltip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

/**
 * Wrapper for adding tooltip to any existing button
 * Usage:
 * <WithTooltip tooltip="Save your changes">
 *   <Button>Save</Button>
 * </WithTooltip>
 */
export function WithTooltip({ children, tooltip, side = "top" }) {
  if (!tooltip) return children;

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          {children}
        </TooltipTrigger>
        <TooltipContent 
          side={side}
          className="bg-slate-900 text-white border-slate-700 max-w-xs"
        >
          <p>{tooltip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
