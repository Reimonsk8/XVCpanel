#pragma once

#include "ofMain.h"

struct Particle {
    ofVec2f pos;
    ofVec2f vel;
    float life;
    float maxLife;
    float size;
    ofColor color;
};

class ofApp : public ofBaseApp {
public:
    void setup() override;
    void update() override;
    void draw() override;
    void keyPressed(int key) override;

private:
    static constexpr int NUM_PARTICLES = 8000;
    std::vector<Particle> particles;
    float time = 0.0f;
    bool paused = false;

    ofFbo fbo;
    ofEasyCam cam;

    void resetParticle(Particle& p);
    ofVec2f curlNoise(ofVec2f p);
};
