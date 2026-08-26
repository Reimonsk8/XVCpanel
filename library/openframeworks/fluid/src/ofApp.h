#pragma once

#include "ofMain.h"

class ofApp : public ofBaseApp {
public:
    void setup() override;
    void update() override;
    void draw() override;
    void mouseDragged(int x, int y, int button) override;
    void keyPressed(int key) override;

private:
    static constexpr int N = 128;
    static constexpr int SIZE = (N + 2) * (N + 2);

    std::vector<float> u, v, u_prev, v_prev;
    std::vector<float> dens, dens_prev;

    float dt = 0.4f;
    float diff = 0.0001f;
    float visc = 0.0f;

    ofFbo fbo;
    std::vector<unsigned char> pixels;

    void addSource(int x, int y, float dx, float dy, float amount);
    void diffuse(int b, std::vector<float>& x, std::vector<float>& x0);
    void advect(int b, std::vector<float>& d, std::vector<float>& d0,
                std::vector<float>& u, std::vector<float>& v);
    void project(std::vector<float>& u, std::vector<float>& v,
                 std::vector<float>& p, std::vector<float>& div);
    void setBnd(int b, std::vector<float>& x);

    int IX(int i, int j) { return i + (N + 2) * j; }
};
