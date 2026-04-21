import { onBeforeUnmount, onMounted } from "vue";


export function useHeartbeat(send: () => Promise<void> | void, intervalMs = 15000) {
  let timer: number | undefined;

  onMounted(() => {
    void send();
    timer = window.setInterval(() => {
      void send();
    }, intervalMs);
  });

  onBeforeUnmount(() => {
    window.clearInterval(timer);
  });
}
