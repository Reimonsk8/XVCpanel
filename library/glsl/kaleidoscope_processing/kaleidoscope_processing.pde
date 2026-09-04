// XVCpanel - Kaleidoscope (Processing GLSL) - OSC controlled
import java.net.*;
import java.nio.*;

PShader shader;
OscIn osc;
String shaderFile = "kaleidoscope.glsl";
long lastMod = 0;

float sectorCount = 12.0;
float rotationSpeed = 0.12;
float colorShift = 0.25;

void settings() {
    size(1920, 1080, P2D);
}

void setup() {
    shader = loadShader(shaderFile);
    lastMod = new File(sketchPath("data"), shaderFile).lastModified();
    osc = new OscIn(9005);
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

    sectorCount = osc.get("/kaleido/sectors", sectorCount);
    rotationSpeed = osc.get("/kaleido/rotate", rotationSpeed);
    colorShift = osc.get("/kaleido/color", colorShift);

    shader.set("resolution", float(width), float(height));
    shader.set("time", millis() / 1000.0);
    shader.set("sectors", sectorCount);
    shader.set("rotateSpeed", rotationSpeed);
    shader.set("colorShift", colorShift);
    shader(shader);
    rect(0, 0, width, height);
    resetShader();

    fill(255);
    textSize(14);
    text("FPS: " + nf(frameRate, 1, 1) + "  [F] fullscreen", 10, height - 10);
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

    // parse OSC float message: "<address>,f <f32 BE>"
    String[] decode(byte[] b, int len) {
        int i = 0;
        String addr = "";
        while (i < len && b[i] != 0) { addr += (char) b[i]; i++; }
        if (addr.length() == 0) return null;
        i = (i + 4) & ~3;              // align
        while (i < len && b[i] != 0) i++; // type tag ",f"
        i = (i + 4) & ~3;              // align
        if (i + 4 > len) return null;
        ByteBuffer bb = ByteBuffer.wrap(b, i, 4).order(ByteOrder.BIG_ENDIAN);
        return new String[]{addr, Float.toString(bb.getFloat())};
    }
}
