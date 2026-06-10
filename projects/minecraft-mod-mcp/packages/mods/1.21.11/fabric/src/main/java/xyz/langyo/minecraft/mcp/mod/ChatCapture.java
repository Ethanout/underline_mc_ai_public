package xyz.langyo.minecraft.mcp.mod;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

public class ChatCapture {

    private static final CopyOnWriteArrayList<String> capturedMessages = new CopyOnWriteArrayList<>();
    private static volatile boolean capturing = false;
    private static volatile long captureStartTime = 0;
    private static volatile int maxCaptureMs = 3000;

    public static void startCapture(int timeoutMs) {
        capturedMessages.clear();
        capturing = true;
        captureStartTime = System.currentTimeMillis();
        maxCaptureMs = timeoutMs;
    }

    public static void onChatMessage(String message) {
        if (capturing) {
            capturedMessages.add(message);
        }
    }

    public static void stopCapture() {
        capturing = false;
    }

    public static boolean isCapturing() {
        return capturing;
    }

    public static List<String> getCapturedMessages() {
        return Collections.unmodifiableList(new ArrayList<>(capturedMessages));
    }

    public static boolean isCaptureTimedOut() {
        return capturing && (System.currentTimeMillis() - captureStartTime) > maxCaptureMs;
    }

    public static String waitAndCollect(int timeoutMs) {
        // DO NOT call startCapture here — it clears messages!
        // The caller should have called startCapture before sending the command.
        long deadline = System.currentTimeMillis() + timeoutMs;
        try {
            while (System.currentTimeMillis() < deadline && !isCaptureTimedOut()) {
                Thread.sleep(50);
            }
        } catch (InterruptedException ignored) {}
        stopCapture();
        List<String> msgs = getCapturedMessages();
        if (msgs.isEmpty()) return "{\"sent\":true,\"response\":[]}";
        StringBuilder sb = new StringBuilder("{\"sent\":true,\"response\":[");
        for (int i = 0; i < msgs.size(); i++) {
            if (i > 0) sb.append(",");
            sb.append("\"").append(msgs.get(i).replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")).append("\"");
        }
        sb.append("]}");
        return sb.toString();
    }
}