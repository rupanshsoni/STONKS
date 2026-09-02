"use client";

import { useEffect, useRef } from "react";
import { getState, streamEvents } from "@/lib/api";
import { useDeskStore } from "@/lib/store";
import Toaster from "./Toaster";

export default function DeskProvider({ children }: { children: React.ReactNode }) {
  const setState = useDeskStore((s) => s.setState);
  const applyEvent = useDeskStore((s) => s.applyEvent);
  const setConnected = useDeskStore((s) => s.setConnected);
  const mounted = useRef(false);

  useEffect(() => {
    if (mounted.current) return;
    mounted.current = true;

    const refresh = () =>
      getState().then(setState).catch(() => undefined);
    refresh();
    const poll = setInterval(refresh, 60000);

    const stop = streamEvents(applyEvent, setConnected);

    return () => {
      clearInterval(poll);
      stop();
    };
  }, [setState, applyEvent, setConnected]);

  return (
    <>
      {children}
      <Toaster />
    </>
  );
}
