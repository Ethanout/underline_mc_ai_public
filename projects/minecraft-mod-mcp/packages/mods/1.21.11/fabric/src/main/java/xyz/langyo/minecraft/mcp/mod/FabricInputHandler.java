package xyz.langyo.minecraft.mcp.mod;

import xyz.langyo.minecraft.mcp.common.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gl.Framebuffer;
import net.minecraft.client.texture.NativeImage;
import net.minecraft.client.util.ScreenshotRecorder;
import net.minecraft.client.util.InputUtil;
import net.minecraft.client.option.KeyBinding;
import net.minecraft.client.option.GameOptions;
import net.minecraft.client.input.KeyInput;
import net.minecraft.client.gui.Click;
import net.minecraft.client.gui.Element;
import net.minecraft.client.gui.screen.ChatScreen;
import net.minecraft.client.gui.screen.GameMenuScreen;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.client.gui.widget.ButtonWidget;
import net.minecraft.client.gui.widget.ClickableWidget;
import net.minecraft.client.input.MouseInput;
import net.minecraft.text.Text;
import net.minecraft.text.TranslatableTextContent;
import org.lwjgl.glfw.GLFW;
import java.io.ByteArrayOutputStream;
import java.nio.channels.Channels;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

public class FabricInputHandler extends ReflectedInputHandler {
    private static volatile long allowGameMenuScreenUntil = 0;
    private static final int MOUSE_LEFT = 0;
    private static final int MOUSE_RIGHT = 1;
    private static final int MOUSE_MIDDLE = 2;

    public FabricInputHandler() {
        super(FabricInputHandler::scheduleOnRenderThread);
    }

    public static boolean shouldAllowGameMenuScreen() {
        return System.currentTimeMillis() < allowGameMenuScreenUntil;
    }

    @Override
    protected Object dispatch(String method, java.util.Map<String, String> params, Object wsClient) {
        if (method.equals("open_chat")) return runOnClientThread(this::openChatScreen);
        if (method.equals("pause_game")) return runOnClientThread(this::openPauseMenu);
        if (method.equals("close_screen")) return runOnClientThread(this::closeCurrentScreen);
        if (method.equals("get_screen_buttons") || method.equals("enumerate_widgets")) {
            return runOnClientThread(this::getScreenButtonsFabric);
        }
        if (method.equals("click_button_index")) {
            int index = 0;
            try { index = Integer.parseInt(params.getOrDefault("index", params.getOrDefault("button_index", "0"))); }
            catch (Exception ignored) {}
            final int buttonIndex = index;
            return runOnClientThread(() -> clickButtonIndexFabric(buttonIndex));
        }
        if (method.equals("key_down") || method.equals("key_up") || method.equals("hold_key")) {
            String key = params.get("key");
            if (key == null || key.isEmpty()) return "{\"error\":\"missing key\"}";
            float hold = readHoldSeconds(params, 0.2f);
            if (method.equals("key_down")) return runOnClientThread(() -> setKeyboardKey(key, true));
            if (method.equals("key_up")) return runOnClientThread(() -> setKeyboardKey(key, false));
            return runOnClientThread(() -> holdKeyboardKey(key, hold));
        }
        if (method.equals("mouse_down") || method.equals("mouse_up") || method.equals("hold_mouse")) {
            int button = parseMouseButton(params.getOrDefault("button", "left"));
            float hold = readHoldSeconds(params, 0.2f);
            if (method.equals("mouse_down")) return runOnClientThread(() -> setMouseButton(button, true));
            if (method.equals("mouse_up")) return runOnClientThread(() -> setMouseButton(button, false));
            return runOnClientThread(() -> holdMouseButton(button, hold));
        }
        if (method.equals("hold_use")) {
            float hold = readHoldSeconds(params, 1.2f);
            return runOnClientThread(() -> useItemFabric(hold));
        }
        if (method.equals("hold_attack")) {
            float hold = readHoldSeconds(params, 1.2f);
            return runOnClientThread(() -> holdAttackFabric(hold));
        }
        if (method.equals("use_item") || method.equals("right_click")) {
            float hold = method.equals("use_item") ? 0.1f : 0.08f;
            String holdStr = params.getOrDefault("hold_seconds", params.getOrDefault("hold", params.getOrDefault("duration", "")));
            if (!holdStr.isEmpty()) {
                try { hold = Float.parseFloat(holdStr); } catch (Exception ignored) {}
            }
            final float holdSeconds = Math.max(0.05f, hold);
            return runOnClientThread(() -> useItemFabric(holdSeconds));
        }
        return super.dispatch(method, params, wsClient);
    }

    private static void scheduleOnRenderThread(Runnable task) {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc != null) {
            mc.execute(task);
        } else {
            task.run();
        }
    }

    private interface JsonSupplier {
        String get();
    }

    private static String runOnClientThread(JsonSupplier supplier) {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return "{\"error\":\"no mc instance\"}";
        if (mc.isOnThread()) return supplier.get();
        CountDownLatch latch = new CountDownLatch(1);
        String[] result = new String[1];
        mc.execute(() -> {
            try {
                result[0] = supplier.get();
            } catch (Exception e) {
                result[0] = "{\"error\":\"" + esc(e.getMessage()) + "\"}";
            } finally {
                latch.countDown();
            }
        });
        try {
            if (!latch.await(5, TimeUnit.SECONDS)) return "{\"error\":\"client thread timeout\"}";
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return "{\"error\":\"interrupted\"}";
        }
        return result[0] != null ? result[0] : "{\"error\":\"no result\"}";
    }

    private static String esc(String s) {
        return s == null ? "" : s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n");
    }

    private static String textKey(Text text) {
        if (text != null && text.getContent() instanceof TranslatableTextContent translatable) {
            return translatable.getKey();
        }
        return "";
    }

    private static String textFallback(Text text) {
        if (text != null && text.getContent() instanceof TranslatableTextContent translatable) {
            String fallback = translatable.getFallback();
            return fallback != null ? fallback : "";
        }
        return "";
    }

    private static String englishForText(Text text) {
        String mapped = englishForKey(textKey(text));
        if (!mapped.isEmpty()) return mapped;
        String fallback = textFallback(text);
        if (!fallback.isEmpty()) return fallback;
        return text != null ? text.getString() : "";
    }

    private static String englishForKey(String key) {
        if (key == null || key.isEmpty()) return "";
        return switch (key) {
            case "menu.returnToGame" -> "Return to Game";
            case "gui.advancements" -> "Advancements";
            case "gui.stats" -> "Statistics";
            case "menu.sendFeedback" -> "Give Feedback";
            case "menu.reportBugs" -> "Report Bugs";
            case "menu.options" -> "Options...";
            case "menu.shareToLan" -> "Open to LAN";
            case "menu.returnToMenu" -> "Save and Quit to Title";
            case "menu.game" -> "Game Menu";
            case "gui.done" -> "Done";
            case "gui.cancel" -> "Cancel";
            case "gui.yes" -> "Yes";
            case "gui.no" -> "No";
            case "chat_screen.title" -> "Chat";
            default -> "";
        };
    }

    private static void appendTextJsonFields(StringBuilder sb, Text text) {
        sb.append(",\"label\":\"").append(esc(text != null ? text.getString() : "")).append("\"")
            .append(",\"label_key\":\"").append(esc(textKey(text))).append("\"")
            .append(",\"label_en\":\"").append(esc(englishForText(text))).append("\"");
    }

    private static String commandSummaryEn(String cmd) {
        if (cmd == null) return "";
        String normalized = cmd.startsWith("/") ? cmd.substring(1) : cmd;
        String lower = normalized.toLowerCase(java.util.Locale.ROOT).trim();
        if (lower.startsWith("time set day")) return "Time set to day";
        if (lower.startsWith("time set night")) return "Time set to night";
        if (lower.startsWith("time query daytime")) return "Queried daytime";
        if (lower.startsWith("give ") && lower.contains("minecraft:arrow")) return "Gave arrows";
        if (lower.startsWith("give ")) return "Item given";
        if (lower.startsWith("item replace ") && lower.contains("minecraft:bow")) return "Equipped bow";
        if (lower.startsWith("item replace ")) return "Item slot replaced";
        if (lower.startsWith("execute if entity ") && lower.contains("minecraft:arrow")) return "Arrow detection command sent";
        if (lower.startsWith("say ")) return "Message sent";
        if (lower.startsWith("tp ") || lower.startsWith("teleport ")) return "Teleported";
        if (lower.startsWith("weather clear")) return "Weather set to clear";
        if (lower.startsWith("weather rain")) return "Weather set to rain";
        return "";
    }

    private static void appendSummaryEn(StringBuilder sb, String cmd) {
        String summary = commandSummaryEn(cmd);
        if (!summary.isEmpty()) sb.append(",\"summary_en\":\"").append(esc(summary)).append("\"");
    }

    private static float readHoldSeconds(java.util.Map<String, String> params, float fallback) {
        String holdStr = params.getOrDefault("hold_seconds", params.getOrDefault("hold", params.getOrDefault("duration", "")));
        if (holdStr == null || holdStr.isEmpty()) return fallback;
        try { return Math.max(0.01f, Float.parseFloat(holdStr)); } catch (Exception ignored) {}
        return fallback;
    }

    private static int parseMouseButton(String button) {
        String b = button == null ? "left" : button.toLowerCase(java.util.Locale.ROOT);
        if (b.equals("right") || b.equals("1")) return MOUSE_RIGHT;
        if (b.equals("middle") || b.equals("2")) return MOUSE_MIDDLE;
        return MOUSE_LEFT;
    }

    @Override
    public String getPlayerInfo() {
        try {
            MinecraftClient mc = MinecraftClient.getInstance();
            if (mc == null) return "{\"error\":\"no mc instance\"}";
            if (mc.player == null) return "{\"error\":\"no player (not in world)\"}";
            var player = mc.player;
            StringBuilder sb = new StringBuilder("{");
            sb.append("\"name\":").append(player.getName() != null ? "\"" + player.getName().getString() + "\"" : "null");
            sb.append(",\"x\":").append(String.format(java.util.Locale.ROOT, "%.2f", player.getX()));
            sb.append(",\"y\":").append(String.format(java.util.Locale.ROOT, "%.2f", player.getY()));
            sb.append(",\"z\":").append(String.format(java.util.Locale.ROOT, "%.2f", player.getZ()));
            sb.append(",\"yaw\":").append(String.format(java.util.Locale.ROOT, "%.2f", player.getYaw()));
            sb.append(",\"pitch\":").append(String.format(java.util.Locale.ROOT, "%.2f", player.getPitch()));
            sb.append(",\"health\":").append(player.getHealth());
            sb.append(",\"hunger\":").append(player.getHungerManager().getFoodLevel());
            sb.append(",\"dimension\":\"").append(mc.world != null ? mc.world.getRegistryKey().getValue().toString() : "unknown").append("\"");
            sb.append("}");
            return sb.toString();
        } catch (Exception e) {
            return "{\"error\":\"" + e.getMessage().replace("\"", "'") + "\"}";
        }
    }

    @Override
    public String getWorldInfo() {
        try {
            MinecraftClient mc = MinecraftClient.getInstance();
            if (mc == null || mc.world == null) return "{\"error\":\"no world\"}";
            var world = mc.world;
            StringBuilder sb = new StringBuilder("{");
            try {
                sb.append("\"world_name\":\"").append(mc.getCurrentServerEntry() != null ? mc.getCurrentServerEntry().address : "local").append("\"");
            } catch (Exception e) {
                sb.append("\"world_name\":\"local\"");
            }
            sb.append(",\"time\":").append(world.getTime());
            sb.append(",\"day_time\":").append(world.getTimeOfDay());
            sb.append(",\"raining\":").append(world.isRaining());
            sb.append(",\"thundering\":").append(world.isThundering());
            try {
                sb.append(",\"difficulty\":\"").append(world.getDifficulty().getName()).append("\"");
            } catch (Exception e) {
                sb.append(",\"difficulty\":\"unknown\"");
            }
            sb.append("}");
            return sb.toString();
        } catch (Exception e) {
            return "{\"error\":\"" + e.getMessage().replace("\"", "'") + "\"}";
        }
    }

    @Override
    public byte[] screenshot() {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return null;
        
        final CountDownLatch latch = new CountDownLatch(1);
        final byte[][] result = {null};
        
        mc.execute(() -> {
            try {
                Framebuffer fb = mc.getFramebuffer();
                if (fb == null) {
                    latch.countDown();
                    return;
                }
                ScreenshotRecorder.takeScreenshot(fb, (ni) -> {
                    try {
                        // 先保存为 PNG
                        java.nio.file.Path tmpPng = java.nio.file.Files.createTempFile("mcp_screenshot", ".png");
                        ni.writeTo(tmpPng);
                        ni.close();
                        
                        // 转换为 JPEG
                        java.awt.image.BufferedImage pngImg = javax.imageio.ImageIO.read(tmpPng.toFile());
                        java.awt.image.BufferedImage jpgImg = new java.awt.image.BufferedImage(pngImg.getWidth(), pngImg.getHeight(), java.awt.image.BufferedImage.TYPE_INT_RGB);
                        jpgImg.createGraphics().drawImage(pngImg, 0, 0, null);
                        
                        java.nio.file.Path tmpJpg = java.nio.file.Files.createTempFile("mcp_screenshot", ".jpg");
                        javax.imageio.ImageIO.write(jpgImg, "jpg", tmpJpg.toFile());
                        result[0] = java.nio.file.Files.readAllBytes(tmpJpg);
                        
                        java.nio.file.Files.deleteIfExists(tmpPng);
                        java.nio.file.Files.deleteIfExists(tmpJpg);
                    } catch (Exception ignored) {
                    } finally {
                        latch.countDown();
                    }
                });
            } catch (Exception e) {
                latch.countDown();
            }
        });
        
        try {
            latch.await(15, TimeUnit.SECONDS);
            return result[0];
        } catch (InterruptedException e) {
            return null;
        }
    }

    private String openChatScreen() {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return "{\"error\":\"no mc instance\"}";
        mc.setScreen(new ChatScreen("", false));
        return "{\"opened\":true,\"screen\":\"ChatScreen\"}";
    }

    private String openPauseMenu() {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return "{\"error\":\"no mc instance\"}";
        allowGameMenuScreenUntil = System.currentTimeMillis() + 1000;
        mc.setScreen(new GameMenuScreen(true));
        return "{\"paused\":true,\"screen\":\"GameMenuScreen\"}";
    }

    private String closeCurrentScreen() {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return "{\"error\":\"no mc instance\"}";
        Screen screen = mc.currentScreen;
        if (screen == null) return "{\"error\":\"no screen to close\"}";
        String name = screen.getClass().getSimpleName();
        try {
            screen.close();
        } catch (Exception e) {
            mc.setScreen(null);
        }
        return "{\"screen_closed\":true,\"was\":\"" + esc(name) + "\"}";
    }

    private String getScreenButtonsFabric() {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return "{\"error\":\"no mc instance\"}";
        Screen screen = mc.currentScreen;
        if (screen == null) return "{\"error\":\"no screen\"}";
        StringBuilder sb = new StringBuilder();
        sb.append("{\"screen\":\"").append(esc(screen.getClass().getSimpleName())).append("\",\"buttons\":[");
        boolean first = true;
        int index = 0;
        for (Element child : screen.children()) {
            if (child instanceof ClickableWidget widget) {
                if (!first) sb.append(",");
                first = false;
                sb.append("{\"index\":").append(index)
                    .append(",\"x\":").append(widget.getX())
                    .append(",\"y\":").append(widget.getY())
                    .append(",\"w\":").append(widget.getWidth())
                    .append(",\"h\":").append(widget.getHeight())
                    .append(",\"active\":").append(widget.active)
                    .append(",\"visible\":").append(widget.visible);
                appendTextJsonFields(sb, widget.getMessage());
                sb.append("}");
                index++;
            }
        }
        sb.append("]}");
        return sb.toString();
    }

    private String clickButtonIndexFabric(int targetIndex) {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return "{\"error\":\"no mc instance\"}";
        Screen screen = mc.currentScreen;
        if (screen == null) return "{\"error\":\"no screen\"}";
        int index = 0;
        for (Element child : screen.children()) {
            if (child instanceof ClickableWidget widget) {
                if (index == targetIndex) {
                    if (!widget.active || !widget.visible) {
                        return "{\"error\":\"button not interactable\",\"index\":" + targetIndex + "}";
                    }
                    Click click = new Click(widget.getX() + widget.getWidth() / 2.0,
                            widget.getY() + widget.getHeight() / 2.0, new MouseInput(0, 0));
                    if (widget instanceof ButtonWidget button) {
                        button.onPress(click);
                    } else {
                        widget.mouseClicked(click, false);
                    }
                    StringBuilder sb = new StringBuilder("{\"clicked\":true,\"index\":").append(targetIndex);
                    appendTextJsonFields(sb, widget.getMessage());
                    sb.append("}");
                    return sb.toString();
                }
                index++;
            }
        }
        return "{\"error\":\"button index out of range\",\"index\":" + targetIndex + ",\"count\":" + index + "}";
    }

    private String setKeyboardKey(String key, boolean pressed) {
        int code = GlfwKeys.keyCode(key);
        if (code < 0) return "{\"error\":\"unknown key\",\"key\":\"" + esc(key) + "\"}";
        KeyInput keyInput = new KeyInput(code, 0, 0);
        InputUtil.Key inputKey = InputUtil.fromKeyCode(keyInput);
        if (pressed) KeyBinding.onKeyPressed(inputKey);
        KeyBinding.setKeyPressed(inputKey, pressed);
        return "{\"key\":\"" + esc(key) + "\",\"pressed\":" + pressed + "}";
    }

    private String holdKeyboardKey(String key, float holdSeconds) {
        String result = setKeyboardKey(key, true);
        if (result.contains("\"error\"")) return result;
        MinecraftClient mc = MinecraftClient.getInstance();
        new Thread(() -> {
            try { Thread.sleep((long) (holdSeconds * 1000)); } catch (InterruptedException ignored) {}
            if (mc != null) mc.execute(() -> setKeyboardKey(key, false));
        }, "MCP-HoldKeyRelease").start();
        return "{\"key\":\"" + esc(key) + "\",\"hold_seconds\":"
                + String.format(java.util.Locale.ROOT, "%.2f", holdSeconds) + "}";
    }

    private String setMouseButton(int button, boolean pressed) {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return "{\"error\":\"no mc instance\"}";
        KeyBinding binding = button == MOUSE_RIGHT ? mc.options.useKey
                : button == MOUSE_MIDDLE ? mc.options.pickItemKey
                : mc.options.attackKey;
        if (pressed) KeyBinding.onKeyPressed(binding.getDefaultKey());
        binding.setPressed(pressed);
        if (!pressed && button == MOUSE_RIGHT && mc.interactionManager != null && mc.player != null) {
            mc.interactionManager.stopUsingItem(mc.player);
        }
        return "{\"button\":" + button + ",\"pressed\":" + pressed + "}";
    }

    private String holdMouseButton(int button, float holdSeconds) {
        String result = setMouseButton(button, true);
        if (result.contains("\"error\"")) return result;
        MinecraftClient mc = MinecraftClient.getInstance();
        new Thread(() -> {
            try { Thread.sleep((long) (holdSeconds * 1000)); } catch (InterruptedException ignored) {}
            if (mc != null) mc.execute(() -> setMouseButton(button, false));
        }, "MCP-HoldMouseRelease").start();
        return "{\"button\":" + button + ",\"hold_seconds\":"
                + String.format(java.util.Locale.ROOT, "%.2f", holdSeconds) + "}";
    }

    private String useItemFabric(float holdSeconds) {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return "{\"error\":\"no mc instance\"}";
        if (mc.player == null) return "{\"error\":\"no player\"}";
        try {
            setMouseButton(MOUSE_RIGHT, true);
            new Thread(() -> {
                try { Thread.sleep((long) (holdSeconds * 1000)); } catch (InterruptedException ignored) {}
                mc.execute(() -> setMouseButton(MOUSE_RIGHT, false));
            }, "MCP-UseItemRelease").start();
            return "{\"using\":true,\"hold_seconds\":" + String.format(java.util.Locale.ROOT, "%.2f", holdSeconds) + "}";
        } catch (Exception e) {
            return "{\"error\":\"" + esc(e.getMessage()) + "\"}";
        }
    }

    private String holdAttackFabric(float holdSeconds) {
        return holdMouseButton(MOUSE_LEFT, holdSeconds);
    }

    @Override
    protected boolean isOnRenderThreadImpl() {
        return MinecraftClient.getInstance().isOnThread();
    }

    @Override
    public void pressKey(String key, float holdSeconds) {
        int code = GlfwKeys.keyCode(key);
        if (code < 0) {
            System.err.println("[FabricInputHandler] pressKey unknown key: " + key);
            return;
        }
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return;
        float hold = holdSeconds > 0 ? holdSeconds : 0.08f;
        KeyInput keyInput = new KeyInput(code, 0, 0);
        InputUtil.Key inputKey = InputUtil.fromKeyCode(keyInput);
        mc.execute(() -> {
            try {
                if (mc.currentScreen != null) {
                    mc.currentScreen.keyPressed(keyInput);
                }
                KeyBinding.onKeyPressed(inputKey);
                KeyBinding.setKeyPressed(inputKey, true);
            } catch (Exception e) {
                System.err.println("[FabricInputHandler] pressKey down error: " + e.getMessage());
            }
        });
        new Thread(() -> {
            try { Thread.sleep((long) (hold * 1000)); } catch (InterruptedException ignored) {}
            mc.execute(() -> {
                try {
                    KeyBinding.setKeyPressed(inputKey, false);
                } catch (Exception e) {
                    System.err.println("[FabricInputHandler] pressKey up error: " + e.getMessage());
                }
            });
        }, "MCP-KeyRelease").start();
    }

    private volatile int[] heldKeys = new int[0];

    private static String extractText(Object item) {
        try {
            for (java.lang.reflect.Method m : item.getClass().getDeclaredMethods()) {
                if (m.getParameterCount() == 0 && net.minecraft.text.Text.class.isAssignableFrom(m.getReturnType())) {
                    m.setAccessible(true);
                    try {
                        Object content = m.invoke(item);
                        if (content instanceof net.minecraft.text.Text) {
                            return ((net.minecraft.text.Text) content).getString();
                        }
                    } catch (Exception ignored) {}
                }
            }
            for (java.lang.reflect.Field f : item.getClass().getDeclaredFields()) {
                if (net.minecraft.text.Text.class.isAssignableFrom(f.getType())) {
                    f.setAccessible(true);
                    try {
                        Object content = f.get(item);
                        if (content instanceof net.minecraft.text.Text) {
                            return ((net.minecraft.text.Text) content).getString();
                        }
                    } catch (Exception ignored) {}
                }
            }
        } catch (Exception ignored) {}
        return null;
    }

    @Override
    public void typeText(String text) {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return;
        if (mc.currentScreen == null) return;
        // Run typing on a background thread and schedule each char on render thread
        new Thread(() -> {
            try {
                for (char ch : text.toCharArray()) {
                    mc.execute(() -> {
                        try {
                            for (java.lang.reflect.Method m : mc.currentScreen.getClass().getDeclaredMethods()) {
                                if (m.getName().equals("charTyped") && m.getParameterCount() >= 2) {
                                    Class<?>[] pt = m.getParameterTypes();
                                    m.setAccessible(true);
                                    if (pt.length == 2 && pt[0] == char.class && pt[1] == int.class) {
                                        m.invoke(mc.currentScreen, ch, 0);
                                    } else if (pt.length >= 2) {
                                        Object charInput = pt[1].getConstructor(char.class).newInstance(ch);
                                        m.invoke(mc.currentScreen, ch, charInput);
                                    }
                                    break;
                                }
                            }
                        } catch (Exception e) {
                            System.err.println("[FabricInputHandler] charType '" + ch + "' error: " + e.getMessage());
                        }
                    });
                    Thread.sleep(30);
                }
            } catch (Exception e) {
                System.err.println("[FabricInputHandler] typeText error: " + e.getMessage());
            }
        }, "MCP-TypeText").start();
    }

    @Override
    public void pasteText(String text) {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return;
        mc.execute(() -> {
            try {
                if (mc.currentScreen != null) {
                    java.lang.reflect.Method m = mc.currentScreen.getClass().getDeclaredMethod("insertText", String.class, boolean.class);
                    m.setAccessible(true);
                    m.invoke(mc.currentScreen, text, false);
                }
            } catch (NoSuchMethodException e) {
                try {
                    java.lang.reflect.Method m = mc.currentScreen.getClass().getDeclaredMethod("insertText", String.class);
                    m.setAccessible(true);
                    m.invoke(mc.currentScreen, text);
                } catch (Exception e2) {
                    System.err.println("[FabricInputHandler] pasteText error: " + e2.getMessage());
                }
            } catch (Exception e) {
                System.err.println("[FabricInputHandler] pasteText error: " + e.getMessage());
            }
        });
    }

    @Override
    public void setViewAngle(float yaw, float pitch) {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null || mc.player == null) return;
        mc.execute(() -> {
            try {
                mc.player.setYaw(yaw);
                mc.player.setPitch(pitch);
            } catch (Exception e) {
                System.err.println("[FabricInputHandler] setViewAngle error: " + e.getMessage());
            }
        });
    }

    @Override
    public void lookDelta(float deltaYaw, float deltaPitch) {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null || mc.player == null) return;
        mc.execute(() -> {
            try {
                mc.player.setYaw(mc.player.getYaw() + deltaYaw);
                mc.player.setPitch(Math.max(-90f, Math.min(90f, mc.player.getPitch() + deltaPitch)));
            } catch (Exception e) {
                System.err.println("[FabricInputHandler] lookDelta error: " + e.getMessage());
            }
        });
    }

    @Override
    public String executeCommand(String command) {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null || mc.player == null) return "{\"error\":\"no player\"}";
        try {
            if (mc.player.networkHandler != null) {
                String cmd = command.startsWith("/") ? command.substring(1) : command;
                java.util.Map<String, Integer> beforeFieldSizes = new java.util.LinkedHashMap<>();
                java.util.Set<String> beforeMessages = new java.util.LinkedHashSet<>();
                try {
                    if (mc.inGameHud != null && mc.inGameHud.getChatHud() != null) {
                        var chatHud = mc.inGameHud.getChatHud();
                        for (java.lang.reflect.Field f : chatHud.getClass().getDeclaredFields()) {
                            f.setAccessible(true);
                            try {
                                Object val = f.get(chatHud);
                                if (val instanceof java.util.List) {
                                    java.util.List<?> list = (java.util.List<?>) val;
                                    beforeFieldSizes.put(f.getName(), list.size());
                                    for (Object item : list) {
                                        String text = extractText(item);
                                        if (text != null) beforeMessages.add(text);
                                    }
                                }
                            } catch (Exception ignored) {}
                        }
                    }
                } catch (Exception e) { System.err.println("[FabricInputHandler] beforeField error: " + e.getMessage()); }
                mc.player.networkHandler.sendChatCommand(cmd);
                long deadline = System.currentTimeMillis() + 3000;
                try {
                    while (System.currentTimeMillis() < deadline) {
                        Thread.sleep(100);
                        java.util.List<String> msgs = ChatCapture.getCapturedMessages();
                        if (!msgs.isEmpty()) break;
                        if (mc.inGameHud != null && mc.inGameHud.getChatHud() != null) {
                            var chatHud = mc.inGameHud.getChatHud();
                            for (java.lang.reflect.Field f : chatHud.getClass().getDeclaredFields()) {
                                if (java.util.List.class.isAssignableFrom(f.getType())) {
                                    f.setAccessible(true);
                                    try {
                                        java.util.List<?> list = (java.util.List<?>) f.get(chatHud);
                                        if (list != null) {
                                            for (Object item : list) {
                                                String text = extractText(item);
                                                if (text != null && !beforeMessages.contains(text)) {
                                                    break;
                                                }
                                            }
                                        }
                                    } catch (Exception ignored) {}
                                }
                            }
                            break;
                        }
                    }
                } catch (InterruptedException ignored) {}
                ChatCapture.stopCapture();
                java.util.List<String> msgs = ChatCapture.getCapturedMessages();
                if (!msgs.isEmpty()) {
                    StringBuilder sb = new StringBuilder("{\"sent\":true");
                    appendSummaryEn(sb, cmd);
                    sb.append(",\"response\":[");
                    for (int i = 0; i < msgs.size(); i++) {
                        if (i > 0) sb.append(",");
                        sb.append("\"").append(msgs.get(i).replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")).append("\"");
                    }
                    sb.append("]}");
                    return sb.toString();
                }
                if (!beforeFieldSizes.isEmpty()) {
                    try {
                        if (mc.inGameHud != null && mc.inGameHud.getChatHud() != null) {
                            var chatHud = mc.inGameHud.getChatHud();
                            java.util.List<String> newMessages = new java.util.ArrayList<>();
                            for (java.lang.reflect.Field f : chatHud.getClass().getDeclaredFields()) {
                                if (java.util.List.class.isAssignableFrom(f.getType())) {
                                    f.setAccessible(true);
                                    try {
                                        java.util.List<?> list = (java.util.List<?>) f.get(chatHud);
                                        if (list != null) {
                                            for (Object item : list) {
                                                String text = extractText(item);
                                                if (text != null && !beforeMessages.contains(text)) {
                                                    newMessages.add(text);
                                                }
                                            }
                                        }
                                    } catch (Exception ignored) {}
                                }
                            }
                            if (!newMessages.isEmpty()) {
                                StringBuilder sb = new StringBuilder("{\"sent\":true");
                                appendSummaryEn(sb, cmd);
                                sb.append(",\"response\":[");
                                for (int i = 0; i < newMessages.size(); i++) {
                                    if (i > 0) sb.append(",");
                                    sb.append("\"").append(newMessages.get(i).replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n")).append("\"");
                                }
                                sb.append("]}");
                                return sb.toString();
                            }
                        }
                    } catch (Exception e) {
                        System.err.println("[FabricInputHandler] chatRead error: " + e.getMessage());
                    }
                }
                StringBuilder sb = new StringBuilder("{\"sent\":true");
                appendSummaryEn(sb, cmd);
                sb.append(",\"command\":\"").append(esc(cmd)).append("\"}");
                return sb.toString();
            }
            return "{\"error\":\"no network handler\"}";
        } catch (Exception e) {
            ChatCapture.stopCapture();
            return "{\"error\":\"" + e.getMessage().replace("\"", "'") + "\"}";
        }
    }

    @Override
    public void scroll(int clicks) {
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return;
        long handle = mc.getWindow().getHandle();
        mc.execute(() -> {
            try {
                GLFW.glfwPostEmptyEvent();
                double delta = clicks * 1.0;
                Object mouseHandler = mc.mouse;
                if (mouseHandler != null) {
                    for (java.lang.reflect.Method m : mouseHandler.getClass().getDeclaredMethods()) {
                        String name = m.getName();
                        if ((name.contains("scroll") || name.equals("lambda$setup$2") || name.equals("lambda$setup$3"))
                            && !java.lang.reflect.Modifier.isStatic(m.getModifiers())) {
                            Class<?>[] pt = m.getParameterTypes();
                            if (pt.length == 3 && pt[0] == long.class && pt[1] == double.class && pt[2] == double.class) {
                                m.setAccessible(true);
                                m.invoke(mouseHandler, handle, 0.0, delta);
                                return;
                            }
                        }
                    }
                }
            } catch (Exception e) {
                System.err.println("[FabricInputHandler] scroll error: " + e.getMessage());
            }
        });
    }
}
