// XVCpanel - Flow Field (Processing) - OSC controlled
import java.net.*;
import java.nio.*;

int W = 1920;
int H = 1080;
int COLS = 120;
int ROWS = 68;

float[] flowField;
ArrayList<PVector> particles;
float zoff = 0;

OscIn osc;
float noiseScale = 0.1;
float flowSpeed = 0.5;
float targetCount = 10000;

void settings() {
    size(1920, 1080);
}

void setup() {
    if (System.getenv("XVC_HEADLESS") != null) surface.setVisible(false);
    background(0);
    flowField = new float[COLS * ROWS];
    particles = new ArrayList<PVector>();
    for (int i = 0; i < (int) targetCount; i++) {
        particles.add(new PVector(random(width), random(height)));
    }
    colorMode(HSB, 360, 100, 100, 100);
    osc = new OscIn(9004);
}

void draw() {
    noiseScale = osc.get("/flow/noise", noiseScale);
    flowSpeed = osc.get("/flow/speed", flowSpeed);
    targetCount = osc.get("/flow/count", targetCount);

    // adjust particle count to OSC target
    while (particles.size() < (int) targetCount) {
        particles.add(new PVector(random(width), random(height)));
    }
    while (particles.size() > (int) targetCount) {
        particles.remove(particles.size() - 1);
    }

    fill(0, 0, 0, 4);
    noStroke();
    rect(0, 0, width, height);

    float scale = constrain(noiseScale, 0.001, 0.1);
    float xoff = 0;
    for (int x = 0; x < COLS; x++) {
        float yoff = 0;
        for (int y = 0; y < ROWS; y++) {
            float angle = noise(xoff, yoff, zoff) * TWO_PI * 2;
            flowField[x + y * COLS] = angle;
            yoff += scale;
        }
        xoff += scale;
    }
    zoff += scale * 0.05;

    float speed = constrain(flowSpeed, 0.1, 2.0);
    for (int i = 0; i < particles.size(); i++) {
        PVector p = particles.get(i);

        int col = (int)(p.x / width * COLS);
        int row = (int)(p.y / height * ROWS);
        col = constrain(col, 0, COLS - 1);
        row = constrain(row, 0, ROWS - 1);

        float angle = flowField[col + row * COLS];
        PVector force = PVector.fromAngle(angle);
        force.mult(speed * 0.5);

        p.add(force);

        if (p.x > width) p.x = 0;
        if (p.x < 0) p.x = width;
        if (p.y > height) p.y = 0;
        if (p.y < 0) p.y = height;

        float hu = (angle / TWO_PI * 360 + frameCount * 0.5) % 360;
        stroke(hu, 80, 90, 40);
        point(p.x, p.y);
    }

    fill(0, 0, 100);
    textSize(14);
    text("FPS: " + nf(frameRate, 1, 1) +
         "  Particles: " + particles.size() +
         "  Press F to fullscreen", 10, height - 10);

    snapshotToFrame();
}

void mouseDragged() {
    int col = (int)(mouseX / width * COLS);
    int row = (int)(mouseY / height * ROWS);
    for (int dx = -2; dx <= 2; dx++) {
        for (int dy = -2; dy <= 2; dy++) {
            int c = constrain(col + dx, 0, COLS - 1);
            int r = constrain(row + dy, 0, ROWS - 1);
            flowField[c + r * COLS] = atan2(mouseY - (r * height / ROWS),
                                             mouseX - (c * width / COLS));
        }
    }
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
    if (key == 'c' || key == 'C') {
        background(0);
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

long lastShot = 0;

// ~4 fps scaled PNG next to the sketch; the panel's [v] preview pane renders it
void snapshotToFrame() {
    if (millis() - lastShot < 250) {
        return;
    }
    lastShot = millis();
    new File(sketchPath("data")).mkdirs();
    PImage full = get();
    PImage small = createImage(320, 180, RGB);
    small.copy(full, 0, 0, width, height, 0, 0, 320, 180);
    small.save("data/frame.png");
}
