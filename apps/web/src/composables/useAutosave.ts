import { onBeforeUnmount, watch, type WatchSource } from "vue";


export function useAutosave<T>(
  source: WatchSource<T>,
  save: (value: T) => Promise<void> | void,
  delay = 600
) {
  let timer: number | undefined;

  const stop = watch(
    source,
    (value) => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        void save(value);
      }, delay);
    },
    { deep: true }
  );

  onBeforeUnmount(() => {
    window.clearTimeout(timer);
    stop();
  });
}
