package xyz.langyo.minecraft.mcp.mod;

import xyz.langyo.minecraft.mcp.common.*;
import net.fabricmc.api.ClientModInitializer;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.text.ClickEvent;
import net.minecraft.text.HoverEvent;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;

public class ModDevMcpMod implements ClientModInitializer {
    public static ModDevMcpMod INSTANCE;
    private McpHttpServer httpServer;
    private ReflectedInputHandler handler;
    volatile String debugUrl = null;
    volatile boolean chatSent = false;
    private long lastFrameCacheTime = 0;

    @Override
    public void onInitializeClient() {
        INSTANCE = this;
        handler = new FabricInputHandler();
        System.err.println("[MCP-MOD] handler class: " + handler.getClass().getName());
        int port = McpConfig.getServerPort();
        httpServer = new McpHttpServer(handler, port);
        new Thread(() -> {
            try {
                Thread.sleep(5000);
                httpServer.start();
                debugUrl = "http://127.0.0.1:" + httpServer.getPort() + "/debug";
                System.out.println("[MCP-MOD] Debug page: " + debugUrl);
            } catch (Exception e) {
                System.err.println("[MCP-MOD] HTTP server failed: " + e.getMessage());
            }
        }, "MCP-HTTP").start();
    }

    private static McpRenderer wrapRenderer(DrawContext ctx) {
        return new McpRenderer() {
            @Override public void fill(int x1, int y1, int x2, int y2, int color) {
                ctx.fill(x1, y1, x2, y2, color);
            }
            @Override public int drawString(Object font, String text, int x, int y, int color, boolean shadow) {
                net.minecraft.client.font.TextRenderer tr = (net.minecraft.client.font.TextRenderer) font;
                ctx.drawText(tr, Text.literal(text), x, y, color, shadow);
                return tr.getWidth(Text.literal(text));
            }
            @Override public int getStringWidth(Object font, String text) {
                net.minecraft.client.font.TextRenderer tr = (net.minecraft.client.font.TextRenderer) font;
                return tr.getWidth(Text.literal(text));
            }
        };
    }

    public void onClientTick() {
        if (INSTANCE == null || INSTANCE.debugUrl == null) return;
        MinecraftClient mc = MinecraftClient.getInstance();
        if (mc == null) return;
        try {
            if (mc.getWindow() != null) {
                ReflectionHelper.setCachedWindowHandle(mc.getWindow().getHandle());
            }
            ReflectionHelper.tickMcpControlMode(mc);
            ReflectionHelper.tickVideoCapture(mc);
        } catch (Exception e) {
            System.err.println("[MCP] tick error: " + e.getMessage());
        }
        if (chatSent) return;
        try {
            if (mc.player != null && mc.inGameHud != null && mc.inGameHud.getChatHud() != null) {
                chatSent = true;
                String url = INSTANCE.debugUrl;
                net.minecraft.text.MutableText message = Text.literal("[MCP] Debug page: ");
                net.minecraft.text.MutableText linkText = Text.literal(url)
                    .styled(style -> style
                        .withColor(Formatting.AQUA)
                        .withUnderline(true)
                        .withClickEvent(new ClickEvent.OpenUrl(java.net.URI.create(url)))
                        .withHoverEvent(new HoverEvent.ShowText(Text.literal("Click to open debug page")))
                    );
                message.append(linkText);
                mc.inGameHud.getChatHud().addMessage(message);
                System.out.println("[MCP] Chat message sent: " + url);
            }
        } catch (Exception e) {
            System.err.println("[MCP] chat error: " + e.getMessage());
        }
    }

    public void onInGameHudRender(DrawContext ctx, float tickDelta) {
        try {
            MinecraftClient mc = MinecraftClient.getInstance();
            if (mc == null) return;
            
            if (debugUrl == null && !ReflectionHelper.isMouseReleaseActive() && !ReflectionHelper.isMcpControlMode()) return;

            if (mc.currentScreen == null && !ReflectionHelper.isScreenshotInProgress()
                    && System.currentTimeMillis() - lastFrameCacheTime > 2000) {
                lastFrameCacheTime = System.currentTimeMillis();
                ReflectionHelper.cacheFrameFromRenderThread(mc);
            }

            if (ReflectionHelper.isMcpControlMode() && mc.currentScreen == null) {
                int w = mc.getWindow().getScaledWidth();
                int h = mc.getWindow().getScaledHeight();
                double mouseXd = mc.mouse.getX() * (double) w / (double) mc.getWindow().getWidth();
                double mouseYd = mc.mouse.getY() * (double) h / (double) mc.getWindow().getHeight();
                int mx = (int) mouseXd;
                int my = (int) mouseYd;
                McpOverlayLogic.renderResumeButton(wrapRenderer(ctx), mc.textRenderer, "Resume", w, h, mx, my);
            }
        } catch (Exception e) {
            System.err.println("[MCP] onInGameHudRender error: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public void onScreenRender(DrawContext ctx, Screen screen, int mouseX, int mouseY, float tickDelta) {
        try {
            MinecraftClient mc = MinecraftClient.getInstance();
            if (mc == null) return;
            if (ReflectionHelper.isScreenshotInProgress()) return;

            int w = mc.getWindow().getScaledWidth();
            int h = mc.getWindow().getScaledHeight();
            double mouseXd = mc.mouse.getX() * (double) w / (double) mc.getWindow().getWidth();
            double mouseYd = mc.mouse.getY() * (double) h / (double) mc.getWindow().getHeight();
            int mx = (int) mouseXd;
            int my = (int) mouseYd;

            if (httpServer != null) {
                int port = httpServer.getPort();
                String portText = "MCP Port: " + port;
                int y = h - 12 - mc.textRenderer.fontHeight * 2;
                ctx.drawText(mc.textRenderer, Text.literal(portText), 2, y, 0xFFFFFFFF, true);
            }

            if (ReflectionHelper.isMcpControlMode()) {
                McpOverlayLogic.renderResumeButton(wrapRenderer(ctx), mc.textRenderer, "Resume", w, h, mx, my);
            } else if (screen != null && mc.world != null) {
                McpOverlayLogic.renderTransferButton(wrapRenderer(ctx), mc.textRenderer, "", w, h, mx, my);
            }
        } catch (Exception e) {
            System.err.println("[MCP] onScreenRender error: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public boolean onMouseClicked(double mx, double my, int button) {
        if (button != 0) return false;
        try {
            MinecraftClient mc = MinecraftClient.getInstance();
            if (mc == null) return false;
            int guiX = (int) mx;
            int guiY = (int) my;
            if (ReflectionHelper.isMcpControlMode()) {
                String result = ReflectionHelper.handleOverlayClick(guiX, guiY, mc);
                if ("resume_manual".equals(result) || "system_menu".equals(result)) {
                    return true;
                }
                return !"blocked".equals(result) && !"cooldown".equals(result) && !"not_in_control_mode".equals(result);
            } else {
                String result = ReflectionHelper.handleTransferOverlayClick(guiX, guiY, mc);
                if ("transfer_to_mcp".equals(result)) {
                    return true;
                }
            }
        } catch (Exception e) {
            System.err.println("[MCP] onMouseClicked error: " + e.getMessage());
        }
        return false;
    }
}
