// XVCpanel - Neon Tunnel (Processing GLSL) - OSC controlled
import java.net.*;
import java.nio.*;

PShader shader;
OscIn osc;
String shaderFile = "neon_tunnel.glsl";
long lastMod = 0;

float ringSpeed = 3.0;
float railSpeed = 0.6;
float pulse = 0.5;

void settings() {
    size(1920, 1080, P2D);
}

void setup() {
    shader = loadShader(shaderFile);
    lastMod = new File(sketchPath("data"), shaderFile).lastModified();
    osc = new OscIn(9006);
}

void reloadShaderIfChanged() {
    long m = new File(sketchPath("data"), shaderFile).lastModified();
    if (m != 0 && m != lastMod) {
        lastMod = m;
        PShader candidate = loadShader(shaderFile);
        if (candidate != null) {
            shader = candidate;
            println("shader reloaded: " + shaderFile);
        } else {
            println("shader compile error - keeping previous shader");
        }
    }
}

void draw() {
    reloadShaderIfChanged();

    ringSpeed = osc.get("/neon/ring", ringSpeed);
    railSpeed = osc.get("/neon/rail", railSpeed);
    pulse = osc.get("/neon/pulse", pulse);

    shader.set("resolution", float(width), float(height));
    shader.set("time", millis() / 1000.0);
    shader.set("ringSpeed", ringSpeed);
    shader.set("railSpeed", railSpeed);
    shader.set("pulse", pulse);
    shader(shader);
    rect(0, 0, width, height);
    resetShader();

    fill(255);
    textSize(14);
    text("FPS: " + nf(frameRate, 1, 1) + "  [F] fullscreen", 10, height - 10);

    snapshotToFrame();
}

long lastShot = 0;

// ~4 fps scaled PNG next to the sketch; the dev.ps1 preview pane renders it (data/frame.png)
void snapshotToFrame() {
    if (millis() - lastShot < 250) {
        return;
    }
    lastShot = millis();
    PImage full = get();
    PImage small = createImage(320, 180, RGB);
    small.copy(full, 0, 0, width, height, 0, 0, 320, 180);
    small.save("data/frame.png");
}

void keyPressed() {
    if (key == 'f' || key == 'F') {
        if (fullscreen) {
            surface.setSize(1920, 1080);
        } else {
            surface.setSize(displayWidth, displayHeight);
        }
        fullscreen = !fullscreen;
    }
}

boolean fullscreen = false;

// --- minimal OSC receiver (background thread), no third-party lib ---
class OscIn extends Thread {
    DatagramSocket sock;
    java.util.Map<String, Float> vals = new java.util.HashMap<>();

    OscIn(int port) {
        try {
            sock = new DatagramSocket(port);
            start();
        } catch (Exception e) {
            println("OSC listen failed on " + port + ": " + e);
        }
    }

    public void run() {
        byte[] buf = new byte[512];
        while (sock != null && !sock.isClosed()) {
            try {
                DatagramPacket p = new DatagramPacket(buf, buf.length);
                sock.receive(p);
                String[] m = decode(buf, p.getLength());
                if (m != null) vals.put(m[0], Float.parseFloat(m[1]));
            } catch (Exception e) {
                // ignore partial/empty packets
            }
        }
    }

    float get(String addr, float def) {
        Float v;
        synchronized (vals) { v = vals.get(addr); }
        return v == null ? def : v;
    }

    String[] decode(byte[] b, int len) {
        int i = 0;
        String addr = "";
        while (i < len && b[i] != 0) { addr += (char) b[i]; i++; }
        if (addr.length() == 0) return null;
        i = (i + 4) & ~3;
        while (i < len && b[i] != 0) i++;
        i = (i + 4) & ~3;
        if (i + 4 > len) return null;
        ByteBuffer bb = ByteBuffer.wrap(b, i, 4).order(ByteOrder.BIG_ENDIAN);
        return new String[]{addr, Float.toString(bb.getFloat())};
    }
}
