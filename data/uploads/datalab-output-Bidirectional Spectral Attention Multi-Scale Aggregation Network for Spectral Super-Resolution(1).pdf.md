

# Bidirectional Spectral Attention Multi-Scale Aggregation Network for Spectral Super-Resolution

**Abstract**—Spectral super-resolution (SSR) refers to reconstructing a hyperspectral image (HSI) from a single RGB image. Recently, deep learning has demonstrated remarkable potential in the field of spectral super-resolution (SSR), achieving impressive results. However, existing deep learning-based approaches often fall short of delivering high-fidelity SSR outcomes. These methods tend to focus primarily on spectral information while overlooking the critical role of spatial features. Furthermore, they lack effective strategies for capturing inter-band relationships, resulting in suboptimal spectral information modeling. To address these limitations, we draw inspiration from inter-frame information utilization in video super-resolution and propose a novel network for SSR, termed Bidirectional Spectral Attention Multi-Scale Aggregation Network (BiSANet). BiSANet features three U-Net-like branches and integrates two advanced attention mechanisms to efficiently and accurately extract and fuse spectral and spatial information through multi-scale, multi-level feature interaction and bidirectional spectral attention modeling. Additionally, a reconstruction module is introduced to adaptively integrate bidirectional spectral features and reconstruct high-quality HSI. Extensive experiments on three publicly available benchmark datasets demonstrate that the proposed method consistently outperforms state-of-the-art SSR methods in both qualitative and quantitative evaluations.

**Index Terms**—Deep learning, Attention mechanism, hyperspectral image (HSI), spectral super-resolution (SSR).

## I. INTRODUCTION

HSI has been widely applied in fields such as remote sensing [1]–[6], food safe [7], [8], environmental monitoring [9]–[11], and geological exploration [12], [13] due to its ability to capture rich spectral information within each pixel. However, due to the limitations of imaging technology, capturing HSI is time-consuming and complex, inevitably restricting the widespread application of HSI in practice.

To overcome the limitations of conventional hyperspectral acquisition systems, one approach is to develop scan-free or snapshot hyperspectral devices based on compressed sensing and computational reconstruction, such as Computed Tomography Imaging Spectrometers (CTIS) [14], hybrid RGB-HS systems [15], and aperture masks [16]. However, these systems still rely heavily on expensive hardware, limiting their practicality. As an alternative, SSR techniques have been proposed to reconstruct high-resolution HSI from RGB images. By leveraging advanced algorithms, SSR reduces the cost of data acquisition and broadens the practical applications of hyperspectral technology, offering a promising alternative to hardware-intensive solutions.

Traditional SSR methods are primarily based on techniques such as spectral basis functions [17] and sparse dictionary [18]. However, these methods are limited by their restricted representational capacity and insufficient generalization performance. As a result, deep learning-based SSR approaches

![Diagram of bidirectional spectral attention modeling. The diagram shows two input features, 'Original Feature' and 'Reversed Feature', entering two 'Spectral attention modeling' blocks. These blocks are connected by a 'Share' mechanism. The outputs are combined via element-wise multiplication (indicated by a circle with an 'x') to produce the 'Output Feature'. A 'Spectral Reversal' arrow points from the Original Feature to the Reversed Feature. A 3D coordinate system on the right indicates 'Spatial' and 'Spectral' dimensions.](768b8ab0d55761b205087c079df1e6e6_img.jpg)

Diagram of bidirectional spectral attention modeling. The diagram shows two input features, 'Original Feature' and 'Reversed Feature', entering two 'Spectral attention modeling' blocks. These blocks are connected by a 'Share' mechanism. The outputs are combined via element-wise multiplication (indicated by a circle with an 'x') to produce the 'Output Feature'. A 'Spectral Reversal' arrow points from the Original Feature to the Reversed Feature. A 3D coordinate system on the right indicates 'Spatial' and 'Spectral' dimensions.

Fig. 1. Diagram of bidirectional spectral attention modeling.

[19]–[27] have gradually gained popularity and achieved impressive results. Nevertheless, these methods still fall short of capturing spectral and spatial information effectively. The reason is that many deep learning models in SSR exhibit the following limitations: **1) Insufficient Exploration of Spectral and Spatial Information:** Many existing methods prioritize spectral reconstruction while neglecting the extraction of fine-grained spatial details. This imbalance often results in blurred or distorted spatial dimensions, compromising the quality of reconstructed hyperspectral images [19], [24], [27]. **2) Inadequate Interaction Between Spectral and Spatial Information:** These methods often lack explicit mechanisms to effectively model the complex interactions between spectral and spatial domains. As a result, the integration of these two types of information remains incomplete, limiting their ability to produce high-quality reconstructions [20], [21].

To comprehensively extract spectral and spatial information and effectively model their complex interactions, this paper proposes a novel framework called Bidirectional Spectral Attention Multi-Scale Aggregation Network (BiSANet). The framework consists of two main modules: the Spectral-Spatial Fusion and Interaction Module (SSFIM) and the Reconstruction Module. SSFIM is composed of the Multi-Spectral Attention Block (MSEB), the Reverse Multi-Spectral Attention Block (RMSEB), and the Multi-Spatial Attention Block (MSAB), all three blocks adopt a U-shaped structure to extract the multi-resolution spectral and spatial contextual information critical for hyperspectral image (HSI) reconstruction. Noticeably, MSEB and RMSEB have the same network structure.

In SSFIM, MSEB and RMSEB jointly extract spectral information. Specifically, MSEB incorporates the Spectral Extraction Block (SEB), centered around the Spectral-wise Multi-head Self-Attention (S-MSA) [24], to capture spectral information along the spectral dimension. Inspired by bidirectional frame extraction techniques in video super-resolution [28],

[29], we introduce bidirectional spectral attention modeling Fig 1. Specifically, we apply a reverse operation along the spectral dimension of the feature maps within the RMSEB module to better capture inter-spectral relationships, thus enabling bidirectional spectral attention. Furthermore, MSEB and RMSEB share weights to achieve bidirectional spectral information complementarity, thereby enhancing the effectiveness of spectral feature extraction.

MSAB integrates the SAB module, featuring Window-based Multi-head Self-attention (W-MSA) and Shifted Window-based Multi-head Self-attention (SW-MSA) [30] as its primary components. To fully utilize the hierarchical relationships between features, an independent RGB image reconstruction branch is designed to inject multi-stage spatial information into MSEB and RMSEB dynamically. This enhances the spectral branch's ability to perceive spatial features. Additionally, to ensure the accuracy of spatial information extraction, an independent reconstruction loss is applied to optimize MSAB.

In the reconstruction module, the spectral information extracted by MSEB and RMSEB is adaptively fused, leveraging the powerful global attention modeling of Vision Mamba [31] and the spectral-spatial self-attention capabilities of CBAM [32].

The main contributions of our work can be summarized as follows.

- We proposed Bidirectional Spectral Attention Multi-Scale Aggregation Network, a novel SSR network designed to efficiently extract and integrate spatial and spectral features to enhance SSR accuracy.
- We introduce the concept of bidirectional spectral attention modeling for the first time in SSFIM. Additionally, an innovative RGB image reconstruction branch is designed to achieve multi-level collaborative fusion of spectral and spatial information, enabling the network to fully exploit both spectral and spatial features.
- Through extensive experiments on three publicly available datasets, our network exhibits state-of-the-art performances compared to other methods.

## II. RELATED WORKS

### A. Hyperspectral Image Acquisition

Traditional hyperspectral imaging systems typically use spectrometers to scan the target step by step in the spatial or spectral dimensions. Common methods include whiskbroom, pushbroom, and band sequential scanners. These techniques are widely used in fields such as remote sensing, environmental monitoring, and medical imaging. For example, whiskbroom and pushbroom methods have been applied to photogrammetry and remote sensing tasks in satellite sensors [33], [34]. However, these methods are time-consuming and cannot meet the demands of dynamic scenes. Additionally, these imaging systems are large in size and not suitable for portable applications. To address these challenges, snapshot compressed imaging (SCI) systems [35]–[37] and computational reconstruction algorithms [38]–[43] have been developed. Among SCI systems, coded aperture snapshot spectral imaging (CASSI) [44] has gained attention due to its compact

design and high efficiency. However, even relatively low-cost SCI systems typically range from tens of thousands to over a hundred thousand dollars, which limits their adoption in the consumer market. This further emphasizes the importance and practical significance of hyperspectral image super-resolution research.

### B. Deep-Learning-Base SSR

Currently, many researchers design various convolutional neural network (CNN)-based models to learn the nonlinear mapping relationship between RGB images and HSI. Xiong *et al.* [45] proposed a unified deep learning framework for hyperspectral image recovery from spectrally undersampled projections and explored different network configurations. This framework is the first to attempt hyperspectral image restoration through CASSI enhancement, serving as an effective alternative to the high-complexity compressed sensing (CS) reconstruction. Shi *et al.* [46] designed HSCNN+ based on their previously proposed HSCNN model and achieved first place in the NTIRE 2018 Spectral Reconstruction Challenge [47]. Stibel *et al.* [48] applied an improved U-Net model to semantic segmentation for this task and won the 4th place in the spectral reconstruction competition. The emergence of the self-attention mechanism [49] and its significant success in the field of computer vision have led most researchers to realize that selectively allocating network resources to the more important regions of feature maps can greatly enhance network performance. Currently, most self-attention works [50], [51] primarily achieve spatial or channel attention mechanisms by compressing spatial or channel dimensions through pooling layers. Peng *et al.* [52] proposed a Pixel Attention (PA) module to adaptively rescale pixel-level features across all feature maps. Li *et al.* [23] investigated adaptive weighted channel attention to integrate the correlation between channels and reallocate channel feature responses, achieving the 1st ranking on the “Clean” track and the 3rd place on the “Real World” track in the NTIRE 2020 Spectral Reconstruction Challenge. Following the outstanding performance of Vision Transformer [53] in the field of computer vision, researchers began to adopt multi-head attention mechanisms to achieve higher-quality hyperspectral reconstruction results [24], [39], [54]. Cai *et al.* [24] proposed spectral intelligent multi-head self-attention based on the spatial sparsity and spectral self-similarity properties of HSI, achieving the 1st place in the NTIRE 2022 Spectral Reconstruction Challenge. However, existing methods still have limitations in extracting spectral and spatial information, as well as in the collaborative fusion of both.

## III. METHODOLOGY

### A. Problem Definition

Let  $X \in \mathbb{R}^{H \times W \times 3}$  represent an RGB image and  $Y \in \mathbb{R}^{H \times W \times C}$  represent an HSI, where  $W$  and  $H$  denote the width and height of the images, respectively, and  $C$  represents the number of spectral bands in the HSI. SSR aims to learn

![Figure 2: Overall framework of BiSANet. (a) BiSANet architecture showing input X being processed through Conv 1x1, GELU, Vision Mamba, and SSFIM modules, followed by a Reconstruction block to produce output Y-hat and X-hat. (b) SSFIM block details showing three parallel branches: MSEB, MSAB, and RMSEB. (c) FFN block details. (d) SAB block details. (e) SEB block details. (f) Reconstruction block details.](1b7d539e02a202c2cf2d97698b911447_img.jpg)

Figure 2 illustrates the overall framework of BiSANet. (a) BiSANet: The input image  $X$  is processed through a series of modules: Conv  $1 \times 1$ , GELU, Vision Mamba, and SSFIM. The output is then passed through a Reconstruction block to produce the final output  $\hat{Y}$  and the reconstructed image  $\hat{X}$ . (b) SSFIM: This block consists of three parallel branches: MSEB, MSAB, and RMSEB. Each branch contains a series of SEB (Spectral Attention Block) and SAB (Spatial Attention Block) modules, with DownSample and UpSample operations. The outputs are fused and then processed by Conv  $1 \times 1$  to produce the final output  $F_{SSFIM}$ . (c) FFN: This block consists of Conv  $1 \times 1$ , GELU, DW Conv  $3 \times 3$ , GELU, and Conv  $1 \times 1$  modules. (d) SAB: This block consists of Layer Norm, W-MSA, Layer Norm, SW-MSA, Layer Norm, and FFN modules, with skip connections. (e) SEB: This block consists of Layer Norm, S-MSA, Layer Norm, and FFN modules, with skip connections. (f) Reconstruction: This block consists of Conv  $1 \times 1$ , Vision Mamba, Conv  $3 \times 3$ , RELU, CBAM, Conv  $3 \times 3$ , and Conv  $1 \times 1$  modules.

Figure 2: Overall framework of BiSANet. (a) BiSANet architecture showing input X being processed through Conv 1x1, GELU, Vision Mamba, and SSFIM modules, followed by a Reconstruction block to produce output Y-hat and X-hat. (b) SSFIM block details showing three parallel branches: MSEB, MSAB, and RMSEB. (c) FFN block details. (d) SAB block details. (e) SEB block details. (f) Reconstruction block details.

Fig. 2. The overall framework of BiSANet. (a) BiSANet. (b) Spectral-Spatial Fusion and Interaction Block. (c) FFN. (d) Spatial Attention Block. (e) Spectral Attention Block. (f) Reconstruction Block.

a mapping function  $f(X; \theta)$  to reconstruct  $Y$  from  $X$ . To achieve this, one commonly minimizes the following function:

$$\arg \min_{\theta} \mathcal{L}_1(f(X; \theta), Y) \quad (1)$$

where  $\mathcal{L}_1$  is a loss function.

In spectral imaging, the response  $I_c(x, y)$  of an RGB camera at the spatial position  $(x, y)$  can be defined as:

$$I_c(x, y) = \int F(x, y, \lambda) S_c(\lambda) d\lambda \quad (2)$$

where  $c \in \{R, G, B\}$  indicates the color channel,  $F(x, y, \lambda)$  represents the spectral radiance at position  $(x, y)$  and wavelength  $\lambda$ , and  $S_c(\lambda)$  denotes the spectral response function for channel  $c$ .

In practical scenarios, since the wavelength range is typically sampled discretely, Eq. 2 can be reformulated as:

$$I_c(x, y) = \sum_n F(x, y, \lambda_n) S_c(\lambda_n) \quad (3)$$

where  $n$  refers to the number of discrete spectral bands.

### B. Our Architecture

The overall framework of the network is shown in Fig. 2(a), given an RGB image  $X$  as the input to the network,

it undergoes shallow feature extraction, fusion and interaction of spatial and spectral information, and finally passes through the reconstruction module to output the HSI  $\hat{Y}$ . In SSFIM, to ensure the accuracy of the extracted spatial information, unlike previous works that integrate spatial information extraction as part of the entire network, we independently design an RGB image reconstruction branch, namely MSAB, to extract spatial information. Additionally, an independent loss function is used to constrain the reconstructed RGB image  $\hat{X}$ , ensuring that the extracted spatial information remains accurate. The following equation can express this process:

$$F_s = GELU(Conv_{1 \times 1}(X)) \quad (4)$$

$$F_{Vim} = VisionMamba(F_s) \quad (5)$$

$$[F_{SSFIM}, \hat{X}] = SSFIM(F_{Vim}) \quad (6)$$

$$Y = F_s + Rec(F_{SSFIM}) \quad (7)$$

where  $GELU$  refers to the  $GELU$  activation function,  $Conv_{1 \times 1}$  represents the convolution operation with a  $1 \times 1$  kernel, Vim refers to Vision Mamba [31], Rec denotes the reconstruction module, and  $F_s$  and  $F_{SSFIM}$  are intermediate features.

Fig. 2(b) illustrates the spatial and spectral information extraction and fusion processes in SSFIM. The module consists of three main branches: MSEB, RMSEB, and MSAB, which are responsible for the extraction and fusion of spectral and spatial information. Specifically, MSEB and RMSEB are used for spectral feature extraction. Inspired by the bidirectional propagation operation from video super-resolution, RMSEB is employed to extract reverse-order features along the spectral dimension, allowing for a more comprehensive extraction of spectral information. MSEB and RMSEB share weights, ensuring that the sequential and reverse spectral features complement each other. MSAB is a specially designed RGB image reconstruction branch, aimed at extracting precise spatial information. All branches adopt a U-Net-like structure, with multiple downsampling and upsampling operations to achieve multi-scale feature extraction, capturing both spatial and spectral information more comprehensively. Moreover, the spatial information extracted at each level by MSAB is equally fused into each level of MSEB and RMSEB, enabling deep fusion of spectral and spatial information.

To simplify the paper and avoid redundancy, we focus solely on the information exchange between MSAB and MSEB, as their interaction mirrors that of MSAB and RMSEB. As illustrated in Fig. 2(b), both MSEB and MSAB adopt a U-shaped architecture. This structure consists of an encoder during the downsampling phase, a bottleneck in the middle, and a decoder during the upsampling phase. Additionally, skip connections are introduced between the encoder and decoder layers to ensure the stability of the training process. The following equation can broadly express this process:

$$F_{\text{SEB}_2} = \text{SEB}(D(F_{\text{SEB}_1}) + D(F_{\text{SAB}_1})) \quad (8)$$

$$F_{\text{SEB}_3} = \text{SEB}(D(F_{\text{SEB}_2}) + D(F_{\text{SAB}_2})) \quad (9)$$

$$F_{s_1} = U(F_{\text{SEB}_3}) + U(F_{\text{SAB}_3}) \quad (10)$$

$$F_{\text{SEB}_4} = \text{SEB}(\text{Conv}_{1 \times 1}(\text{Cat}(F_{s_1}, F_{\text{SEB}_2}))) \quad (11)$$

$$F_{s_2} = U(F_{\text{SEB}_4}) + U(F_{\text{SAB}_4}) \quad (12)$$

$$F_{\text{SEB}_5} = \text{SEB}(\text{Conv}_{1 \times 1}(\text{Cat}(F_{s_2}, F_{\text{SEB}_1}))) \quad (13)$$

$$F_{\text{SSFIM}} = \text{Cat}(F_{\text{SEB}_5}, F_{\text{RSEB}_5}) \quad (14)$$

$$\hat{X} = \text{MSAB}(X), \quad (15)$$

where  $D$  and  $U$  represent the downsampling and upsampling operation,  $\text{Cat}$  represents the concatenation operation performed along the spectral dimension.  $F_{s_1}$  and  $F_{s_2}$  represent the intermediate feature maps obtained during the information interaction process. By leveraging multi-level extraction and interaction of spectral and spatial information, the proposed approach comprehensively captures the spectral and spatial features from a multi-scale perspective.

As shown in Fig. 2(f), we designed a novel reconstruction module. By leveraging the powerful global modeling capabilities of Vision Mamba [31] and the CBAM attention mechanism [32], the proposed module effectively utilizes the feature information extracted by SSFIM to accurately reconstruct the

target HSI. The following equation can broadly express this process:

$$\hat{Y} = \text{Rec}(F_{\text{SSFIM}}) \quad (16)$$

where  $\text{Rec}$  represents the Reconstruction Block,  $\hat{Y}$  represents the finally output HSI.

### C. SEB and SAB

As illustrated in Fig. 2(d) and Fig. 2(e), to efficiently establish the correlation and connection between spectral and spatial information, we incorporated S-MSA [24] into the MSEB module. Additionally, Window-based Multi-head Self-attention (W-MSA) and Shifted Window-based Multi-head Self-attention (SW-MSA) [30] were introduced into the MSAB module.

![Figure 3: Paradigms of different Self-attention mechanisms. (a) Spectral Self-Attention: A stack of feature maps is shown, with a bracket labeled 'Token' indicating that each channel is treated as a token. (b) Spatial Self-Attention: A 3D grid of pixels is shown, with a bracket labeled 'Token' indicating that each pixel value within a fixed-size window is treated as a token. A 3D coordinate system is shown with 'Spatial' on the horizontal axis and 'Spectral' on the vertical axis.](8e85c350ee10ead46f7834b148b8b7d3_img.jpg)

Figure 3: Paradigms of different Self-attention mechanisms. (a) Spectral Self-Attention: A stack of feature maps is shown, with a bracket labeled 'Token' indicating that each channel is treated as a token. (b) Spatial Self-Attention: A 3D grid of pixels is shown, with a bracket labeled 'Token' indicating that each pixel value within a fixed-size window is treated as a token. A 3D coordinate system is shown with 'Spatial' on the horizontal axis and 'Spectral' on the vertical axis.

Fig. 3. The paradigms of different Self-attention mechanisms. (a) Each channel is treated as a token, and self-attention is computed along the channel dimension; (b) Each pixel value within a fixed-size window is treated as a token, and self-attention is computed within the window.

As illustrated in Fig. 3(a), in the Spectral Extraction Block (SEB), each channel of the feature map is treated as a token. Let the input feature map be defined as  $X_{\text{in}} \in \mathbb{R}^{H \times W \times C}$ , where  $H$ ,  $W$ , and  $C$  represent the height, width, and number of channels, respectively. The feature map is first reshaped into  $X_{\text{token}} \in \mathbb{R}^{HW \times C}$ , where each token corresponds to a single channel of the feature map. Then,  $X_{\text{token}}$  is projected into query ( $Q$ ), key ( $K$ ), and value ( $V$ ) matrices using the learnable projection matrices  $W_Q$ ,  $W_K$ , and  $W_V$ , where  $W_Q$ ,  $W_K$ , and  $W_V \in \mathbb{R}^{C \times C}$ , as defined below:

$$Q = X_{\text{token}} W_Q \quad (17)$$

$$K = X_{\text{token}} W_K \quad (18)$$

$$V = X_{\text{token}} W_V \quad (19)$$

The query, key, and value matrices are subsequently fed into  $n$ -head self-attention to compute the spectral attention. The process can be summarized mathematically as:

$$A_i^{\text{spectral}} = \text{Softmax}(\mu_i Q_i K_i^\top) \quad (20)$$

$$\text{Output}_i = A_i^{\text{spectral}} V_i \quad (21)$$

$$S\text{-MSA}(X_{\text{token}}) = \text{Cat}_{\text{head}}^i(\text{Output}_i)W + \text{PE}(V) \quad (22)$$

where  $A \in \mathbb{R}^{HW \times HW}$  represents the attention score matrix,  $\mu_i$  is a learnable parameter,  $W \in \mathbb{R}^{C \times C}$  is a learnable projection matrix used to project the concatenated outputs of

all heads back to the original feature dimensionality,  $PE(\cdot)$  represents positional encoding, which incorporates positional information into the features, and  $S-MSA(x_{\text{token}}) \in \mathbb{R}^{HW \times C}$  is the final output of the multi-head self-attention mechanism.

As shown in Fig. 3(b), the input feature map is spatially divided into multiple windows, each containing  $M \times M$  pixels. In the SAB module, each window is treated as a token. Before being processed, the input feature map is reshaped to  $x'_{\text{token}} \in \mathbb{R}^{(HW/M^2) \times M^2 \times C}$ . The number of windows for W-MSA and SW-MSA is set to 8, with 4 shifted windows applied in SW-MSA. Other steps follow those in the SEB and are omitted for brevity.

### D. Reconstruction Block

For the reconstruction module, considering that the inputs of MSEB and RMSEB are the sequential spectral feature map  $F_{\text{Vim}}$  and the reverse-order spectral feature map  $F_{\text{Vim(R)}}$ , respectively, we aim to enable the network to adaptively fuse the complementary spectral information from the two output feature maps  $F_{\text{SEB}_5}$  and  $F_{\text{RSEB}_5}$ . Given the well-known bidirectional propagation capability and global attention of Vision Mamba, as well as the spectral and spatial attention mechanisms provided by CBAM, we incorporate both Vision Mamba and CBAM into the reconstruction module. This design ensures that the network adaptively focuses on the beneficial parts of the features for effective fusion and reconstruction.

### E. Loss Function

To ensure the spectral and spatial accuracy of the reconstructed hyperspectral image (HSI), we employ the  $L_1$  loss function as a constraint. This loss encourages the network to minimize the absolute differences between the predicted and ground truth HSIs, effectively preserving fine-grained spectral and spatial details. Additionally, within the MSAB, a separate  $L_1$  reconstruction loss is applied to ensure the precision of spatial information extracted from the RGB input. By optimizing this independent loss, the MSAB can focus on accurately modeling spatial features while simultaneously supporting the spectral reconstruction process. The following equation can express this process:

$$L_{HSI} = L_1(Y, \hat{Y}), \quad (23)$$

$$L_{RGB} = L_1(X, \hat{X}), \quad (24)$$

$$L_{Final} = \alpha L_{HSI} + \beta L_{RGB} \quad (25)$$

where  $\alpha$  and  $\beta$  are trade-off weights.

## IV. EXPERIMENTS

### A. Datasets

We use three datasets in experiments. **ICVL** dataset consists of 201 images, each containing 31 spectral channels. We randomly selected 184 images as the training set and 6 images as the test set. Before the experiment, each image was cropped to (31, 256, 256). **DFC2018 Houston** dataset contains 50 spectral channels. For this experiment, 92 images

were randomly selected as the training set and 6 images as the test set. **TG1HRSSC** dataset comprises three types of data: panchromatic images, visible near-infrared images with 54 effective bands, and short-wave infrared images with 52 effective bands. For this experiment, we chose the visible near-infrared images, randomly selecting 40 images as the training set and 6 images as the test set.

### B. Experimental Settings

**Evaluation Metrics.** We use three key evaluation metrics to objectively assess and compare the performance of the various methods: Peak Signal-to-Noise Ratio (PSNR), Structural Similarity Index (SSIM), and Spectral Angle Mapper (SAM). These metrics are well-established in the fields of image processing for evaluating image quality, fidelity, and spectral accuracy.

$$MSE = \frac{1}{N} \sum_{i=0}^N \|x_i - y_i\|^2, \quad (26)$$

$$PSNR = 10 \cdot \log_{10} \left( \frac{MAX_I^2}{MSE} \right), \quad (27)$$

where  $MAX_I$  is the maximum pixel value, for example, if each sample point is expressed in 8 bits,  $MAX_I$  is 255.  $x$  and  $y$  are the two images that are compared.  $N$  is the number of pixels  $x$  in and  $y$ .

$$SSIM = \frac{(2\mu_x\mu_y + c_1)(\sigma_{xy} + c_2)}{(\mu_x^2 + \mu_y^2 + c_1)(\sigma_x^2 + \sigma_y^2 + c_2)}, \quad (28)$$

where  $\mu_x$  and  $\mu_y$  represent the means of  $x$  and  $y$ ,  $\sigma_x$  and  $\sigma_y$  are variances,  $\sigma_{xy}$  is the covariance, and  $c_1$ ,  $c_2$  are manual constants.

$$SAM = \frac{1}{N} \sum_{i=1}^N \arccos\left(\frac{x_i^T y_i}{\|x_i\| \|y_i\|}\right), \quad (29)$$

where  $N$  is the number of pixels of  $x$  and  $y$ .

### C. Main Results

We compared our approach with six state-of-the-art methods: SSRNet [19], MST++ [24], MSFN [20], HSRNet [22], HSACS [21] and AWAN [23].

**Quantitative Results.** As shown in Table I, we compare the performance using three selected metrics, which represent the average values tested on the dataset. The best and second-best performances are highlighted in red and bold, respectively. Across all three datasets, our BiSANet consistently outperforms the compared SSR methods, demonstrating strong competitiveness. For the ICVL dataset, our method achieves 0.37% and 0.03% higher PSNR and SSIM, respectively, and 1.48% lower SAM than the second-best method. For the DFC2018 Houston dataset, our method outperforms the second-best method by 4.26% in PSNR, 0.16% in SSIM, and achieves 11.52% lower SAM. For the TG1HRSSC dataset, the improvements are 0.55% in PSNR, 0.30% in SSIM, and 1.18% lower SAM, the significant advantages in PSNR

TABLE I  
FINAL TESTING RESULTS OF ICVL, DFC2018 HOUSTON, AND TG1HRS SC. THE BEST AND SECOND-BEST RESULTS ARE HIGHLIGHTED IN RED AND BOLD, RESPECTIVELY. ↑ THE HIGHER THE BETTER, AND VICE VERSA.

| Dataset         |       | Ours           | SSRNet        | MST++   | MSFN           | HSRNet  | HSACS          | AWAN    |
|-----------------|-------|----------------|---------------|---------|----------------|---------|----------------|---------|
| ICVL            | PSNR↑ | <b>29.5380</b> | 29.1559       | 29.1772 | 29.0833        | 29.2239 | <b>29.4291</b> | 28.6324 |
|                 | SSIM↑ | <b>0.8721</b>  | 0.8699        | 0.8693  | 0.8652         | 0.8618  | <b>0.8718</b>  | 0.8421  |
|                 | SAM↓  | <b>7.0733</b>  | 7.3821        | 7.3895  | 7.5215         | 7.3656  | <b>7.1797</b>  | 7.7500  |
| DFC2018 Houston | PSNR↑ | <b>31.4634</b> | 26.5621       | 29.5294 | <b>30.1771</b> | 28.5730 | 29.8760        | 29.9709 |
|                 | SSIM↑ | <b>0.9501</b>  | 0.9409        | 0.9416  | 0.9418         | 0.9104  | <b>0.9486</b>  | 0.9468  |
|                 | SAM↓  | <b>7.3471</b>  | 12.0027       | 9.0179  | 8.5957         | 10.4958 | <b>8.3038</b>  | 8.7143  |
| TG1HRS SC       | PSNR↑ | <b>28.6264</b> | 26.9268       | 28.3167 | <b>28.4690</b> | 27.0887 | 27.8440        | 27.0703 |
|                 | SSIM↑ | <b>0.9091</b>  | <b>0.9064</b> | 0.8718  | 0.8954         | 0.8896  | 0.8940         | 0.8806  |
|                 | SAM↓  | <b>6.0575</b>  | 7.3815        | 6.3581  | <b>6.1298</b>  | 7.3842  | 6.5715         | 7.9552  |

![Figure 4: Visualization results of seven methods on the ICVL dataset. The figure is a grid of images. The first row shows the Ground Truth (GT) pseudo-color images. The second row shows the corresponding error maps for the GT. The third row shows the pseudo-color images generated by the 'Ours' method. The fourth row shows the error maps for the 'Ours' method. The fifth row shows the pseudo-color images generated by the 'SSRNet' method. The sixth row shows the error maps for the 'SSRNet' method. The seventh row shows the pseudo-color images generated by the 'MST++' method. The eighth row shows the error maps for the 'MST++' method. The ninth row shows the pseudo-color images generated by the 'MSFN' method. The tenth row shows the error maps for the 'MSFN' method. The eleventh row shows the pseudo-color images generated by the 'HSRNet' method. The twelfth row shows the error maps for the 'HSRNet' method. The thirteenth row shows the pseudo-color images generated by the 'HSACS' method. The fourteenth row shows the error maps for the 'HSACS' method. The fifteenth row shows the pseudo-color images generated by the 'AWAN' method. The sixteenth row shows the error maps for the 'AWAN' method. Each pseudo-color image has a red rectangle highlighting a specific region. The error maps use a color scale from blue (low error) to red (high error). The 'Ours' method shows significantly lower error (more blue) compared to the other methods.](46f43cb4ffd47565e7c0ca306d461435_img.jpg)

Figure 4: Visualization results of seven methods on the ICVL dataset. The figure is a grid of images. The first row shows the Ground Truth (GT) pseudo-color images. The second row shows the corresponding error maps for the GT. The third row shows the pseudo-color images generated by the 'Ours' method. The fourth row shows the error maps for the 'Ours' method. The fifth row shows the pseudo-color images generated by the 'SSRNet' method. The sixth row shows the error maps for the 'SSRNet' method. The seventh row shows the pseudo-color images generated by the 'MST++' method. The eighth row shows the error maps for the 'MST++' method. The ninth row shows the pseudo-color images generated by the 'MSFN' method. The tenth row shows the error maps for the 'MSFN' method. The eleventh row shows the pseudo-color images generated by the 'HSRNet' method. The twelfth row shows the error maps for the 'HSRNet' method. The thirteenth row shows the pseudo-color images generated by the 'HSACS' method. The fourteenth row shows the error maps for the 'HSACS' method. The fifteenth row shows the pseudo-color images generated by the 'AWAN' method. The sixteenth row shows the error maps for the 'AWAN' method. Each pseudo-color image has a red rectangle highlighting a specific region. The error maps use a color scale from blue (low error) to red (high error). The 'Ours' method shows significantly lower error (more blue) compared to the other methods.

Fig. 4. The visualization results of seven methods on the ICVL dataset are presented. The first and third rows depict pseudo-color images generated from the HSIs. The second and fourth rows illustrate the error maps, which represent the discrepancies between the network-generated images and the ground truth. In these error maps, blue shades correspond to smaller errors, indicating higher accuracy.

and SAM demonstrate the outstanding performance of our network in spectral information recovery. This exceptional capability is primarily attributed to several innovative designs in our network. Firstly, bidirectional spectral attention modeling allows for the comprehensive capture of correlations in the spectral dimension, enabling more precise restoration of spectral features. Furthermore, the integration of independent spatial loss modeling provides additional supervisory signals from the spatial dimension, further enhancing the network's ability to recover spectral information. Additionally, the multi-level fusion mechanism of spectral and spatial information plays a crucial role. By progressively fusing spectral and spatial features at different scales, this mechanism strengthens the synergy between spectral and spatial information. Such a

design not only improves the accuracy of spectral recovery but also significantly enhances the network's adaptability to complex scenarios and fine details, ultimately achieving efficient interaction and precise modeling of spectral and spatial information.

**Qualitative Results.** Fig 4, Fig 5, and Fig 6 illustrate the visualization results of the ICVL, DFC2018 Houston, and TG1HRS SC datasets. The first and third rows display the pseudo-color images generated from the hyperspectral images, while the second and fourth rows present the spectral angle error maps. In the error maps, blue areas indicate smaller errors, whereas red areas signify larger errors. From the visualizations, it is evident that our network produces high-quality pseudo-color images closely matching the ground truth, while

![Figure 5: Visualization results of seven methods on the DFCHouston2018 dataset. The figure is a grid of images. The first row shows pseudo-color images generated from the HSIs for GT, Ours, SSRNet, MST++, MSFN, HSRNet, HSACS, and AWAN. The second row shows error maps for the same methods, with a color bar on the right indicating error levels from Low (blue) to High (red). The third row shows another set of pseudo-color images, and the fourth row shows their corresponding error maps. The 'Ours' method consistently shows lower error maps (more blue) compared to the other methods.](9ebd85380ef496499e5f23ec0d9cd744_img.jpg)

Figure 5: Visualization results of seven methods on the DFCHouston2018 dataset. The figure is a grid of images. The first row shows pseudo-color images generated from the HSIs for GT, Ours, SSRNet, MST++, MSFN, HSRNet, HSACS, and AWAN. The second row shows error maps for the same methods, with a color bar on the right indicating error levels from Low (blue) to High (red). The third row shows another set of pseudo-color images, and the fourth row shows their corresponding error maps. The 'Ours' method consistently shows lower error maps (more blue) compared to the other methods.

Fig. 5. The visualization results of seven methods on the DFCHouston2018 dataset are presented. The first and third rows depict pseudo-color images generated from the HSIs. The second and fourth rows illustrate the error maps, which represent the discrepancies between the network-generated images and the ground truth. In these error maps, blue shades correspond to smaller errors, indicating higher accuracy.

TABLE II  
QUANTITATIVE RESULTS OF ABLATION EXPERIMENTS ON THE TG1HRSSC DATASET. THE BEST AND SECOND-BEST RESULTS ARE HIGHLIGHTED IN RED AND BOLD, RESPECTIVELY.

| Model   | RMSEB | Weight Share | Reconstruction | $L_{RGB}$ | PSNR $\uparrow$ | SSIM $\uparrow$ | SAM $\downarrow$ |
|---------|-------|--------------|----------------|-----------|-----------------|-----------------|------------------|
| 1       | ✗     | ✓            | ✓              | ✓         | <b>27.9682</b>  | 0.8951          | <b>6.5189</b>    |
| 2       | ✓     | ✗            | ✓              | ✓         | 26.6399         | <b>0.9065</b>   | 7.3411           |
| 3       | ✓     | ✓            | ✗              | ✓         | 26.5343         | 0.8862          | 8.0959           |
| 4       | ✓     | ✓            | ✓              | ✗         | 26.1646         | 0.8755          | 8.6879           |
| BiSANet | ✓     | ✓            | ✓              | ✓         | <b>28.6264</b>  | <b>0.9091</b>   | <b>6.0575</b>    |

other methods often exhibit issues such as color distortion or overall blurring, especially in detailed and edge regions. Additionally, in the error maps, our network demonstrates superior performance across various regions compared to the six other SSR methods, achieving precise reconstruction even in challenging areas. These advantages are attributed to the bidirectional spectral attention modeling and multi-level spectral-spatial information fusion within our network, enabling comprehensive and accurate spectral-spatial information integration and resulting in outstanding reconstruction performance. To further validate the effectiveness of our network, we plotted the spectral curves of the reconstructed HSI based on randomly selected pixels, comparing them with the ground truth. Each curve corresponds to an SSR method or the ground truth. As shown in Fig. 7, the spectral curves generated by our BiSANet exhibit a high degree of correlation with the ground truth. Our method accurately captures the major spectral characteristics and closely aligns with the ground truth

in finer spectral details. These findings further confirm our network's powerful performance and reliability in SSR tasks.

### D. Ablation Analysis

We designed four BiSANet variants to test our proposed components' effectiveness.

**Variant 1:** To evaluate the importance of bidirectional spectral attention modeling, we removed the RMSEB module and replaced it with MSEB, making both spectral branches process input feature maps in the same sequential spectral order. As shown in Table 3, PSNR and SSIM decreased by 2.30% and 1.54%, respectively, while SAM increased by 7.62%. These results demonstrate that bidirectional spectral attention modeling enables more efficient spectral information capture.

**Variant 2:** To test the significance of weight sharing between MSEB and RMSEB, we removed the shared weights and trained the two spectral branches independently. Table 3 shows that PSNR and SSIM decreased by 6.94% and 0.29%,

![Figure 6: Visualization results of seven methods on the TG1HRSSC dataset. The figure is a grid of images. The first row shows pseudo-color images generated from the HSIs for GT, Ours, SSRNet, MST++, MSFN, HSRNet, HSACS, and AWAN. The second row shows error maps for the same methods, with a color bar on the right indicating error levels from L (blue) to H (red). The third row shows another set of pseudo-color images, and the fourth row shows their corresponding error maps. Red boxes highlight specific regions in the images for comparison.](892f25e3d71d8e315a2a51092a8a8da7_img.jpg)

Figure 6: Visualization results of seven methods on the TG1HRSSC dataset. The figure is a grid of images. The first row shows pseudo-color images generated from the HSIs for GT, Ours, SSRNet, MST++, MSFN, HSRNet, HSACS, and AWAN. The second row shows error maps for the same methods, with a color bar on the right indicating error levels from L (blue) to H (red). The third row shows another set of pseudo-color images, and the fourth row shows their corresponding error maps. Red boxes highlight specific regions in the images for comparison.

Fig. 6. The visualization results of seven methods on the TG1HRSSC dataset are presented. The first and third rows depict pseudo-color images generated from the HSIs. The second and fourth rows illustrate the error maps, which represent the discrepancies between the network-generated images and the ground truth. In these error maps, blue shades correspond to smaller errors, indicating higher accuracy.

![Figure 7: Spectral curves of randomly picked pixels from HSIs reconstructed by the compared methods. The figure contains three subplots: (a) for the ICVL dataset, (b) for the DFC2018 Houston dataset, and (c) for the TG1HRSSC dataset. Each subplot shows Normalized Intensity (y-axis, 0.0 to 0.8) versus Channel (x-axis, 0 to 50). The legend includes: AWAN, HSACS, HSRNet, MSFN, MST++, SSRNet, Groundtruth, and BiSANet. The Groundtruth curve is a solid green line, and the other methods are represented by dashed lines of various colors.](d864789b0d8384da1d22fd6a5d76bbdf_img.jpg)

Figure 7: Spectral curves of randomly picked pixels from HSIs reconstructed by the compared methods. The figure contains three subplots: (a) for the ICVL dataset, (b) for the DFC2018 Houston dataset, and (c) for the TG1HRSSC dataset. Each subplot shows Normalized Intensity (y-axis, 0.0 to 0.8) versus Channel (x-axis, 0 to 50). The legend includes: AWAN, HSACS, HSRNet, MSFN, MST++, SSRNet, Groundtruth, and BiSANet. The Groundtruth curve is a solid green line, and the other methods are represented by dashed lines of various colors.

Fig. 7. Spectral curves of randomly picked pixels from HSIs reconstructed by the compared methods. (a), (b), and (c) spectral curves are derived from test set images partitioned from the ICVL, DFC2018 Houston, and TG1HRSSC datasets, respectively.

respectively, while SAM increased by 7.62%. This indicates that the spectral information extracted by the two spectral attention branches is complementary rather than conflicting. Joint training enables more effective and accurate spectral information extraction.

**Variant 3:** To assess the effectiveness of the proposed reconstruction module, we replaced it with a module based on the ResNet architecture. As shown in Table 3, PSNR and SSIM dropped by 7.31% and 2.52%, respectively, while SAM increased by 33.65%. This performance gap highlights the superiority of our reconstruction module, attributed to the integration of Vision Mamba for global information modeling and adaptive bidirectional spectral information fusion. Additionally, CBAM facilitates attention extraction and fusion in both spectral and spatial dimensions, achieving highly accurate

reconstruction results.

**Variant 4:** To test the effectiveness of the independent reconstruction loss in MSAB, we removed  $L_{\text{RGB}}$ . As shown in Table 3, PSNR and SSIM decreased by 8.60% and 3.70%, respectively, while SAM increased by 43.42%. These results reveal the importance of precise spatial information for spectral information acquisition and HSI reconstruction. By incorporating multi-level spatial information injection and independent reconstruction loss, our network efficiently extracts and integrates spatial information, laying a solid foundation for subsequent HSI reconstruction.

From the above ablation experiments, it is evident that our network effectively captures spectral information. The precise and efficient spatial information injection and the seamless fusion of spatial and spectral information enable our network

to achieve state-of-the-art performance in HSI reconstruction quality.

## V. CONCLUSION

In this paper, we present a novel deep learning framework, BiSANet, designed to tackle the challenging task of hyperspectral image (HSI) reconstruction. Inspired by video super-resolution techniques, our network pioneers the concept of bidirectional spectral attention modeling. Through the integration of MSEB and RMSEB modules, BiSANet effectively captures complementary spectral information. The reconstruction module leverages the strengths of Vision Mamba and CBAM, enabling adaptive fusion of spectral and spatial features. Furthermore, the MSAB combined with an independent reconstruction loss, significantly improves spatial feature extraction, delivering essential spatial context information for accurate and high-quality HSI reconstruction. Quantitative and qualitative experiments conducted on three publicly available datasets demonstrate that our network outperforms other state-of-the-art SSR methods.

## REFERENCES

- [1] J. M. Bioucas-Dias, A. Plaza, G. Camps-Valls, P. Scheunders, N. Nasrabadi, and J. Chanussot, "Hyperspectral remote sensing data analysis and future challenges," *IEEE Geosci. Remote Sens. Mag.*, vol. 1, no. 2, pp. 6–36, 2013.
- [2] R. Dian, S. Li, B. Sun, and A. Guo, "Recent advances and new guidelines on hyperspectral and multispectral image fusion," *Information Fusion*, vol. 69, pp. 40–51, 2021.
- [3] L. Zhang, J. Nie, W. Wei, Y. Li, and Y. Zhang, "Deep blind hyperspectral image super-resolution," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 32, no. 6, pp. 2388–2400, 2020.
- [4] W. Wang, X. Fu, W. Zeng, L. Sun, R. Zhan, Y. Huang, and X. Ding, "Enhanced deep blind hyperspectral image fusion," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 34, no. 3, pp. 1513–1523, 2021.
- [5] J. Li, Z. Zhang, R. Song, Y. Li, and Q. Du, "Scformer: Spectral coordinate transformer for cross-domain few-shot hyperspectral image classification," *IEEE Trans. Image Process.*, vol. 33, pp. 840–855, 2024.
- [6] J. Li, Y. Liu, R. Song, Y. Li, K. Han, and Q. Du, "Sal<sup>2</sup>rn: A spatial-spectral salient reinforcement network for hyperspectral and lidar data fusion classification," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, pp. 1–14, 2022.
- [7] H. Pu, L. Lin, and D.-W. Sun, "Principles of hyperspectral microscope imaging techniques and their applications in food quality and safety detection: A review," *Compr. Rev. Food Sci. Food Saf.*, vol. 18, no. 4, pp. 853–866, 2019.
- [8] A. A. Gowen, C. P. O'Donnell, P. J. Cullen, G. Downey, and J. M. Frias, "Hyperspectral imaging—an emerging process analytical tool for food quality and safety control," *Trends in food science & technology*, vol. 18, no. 12, pp. 590–598, 2007.
- [9] Y. Wang, Q. Yuan, T. Li, and L. Zhu, "Global spatiotemporal estimation of daily high-resolution surface carbon monoxide concentrations using deep forest," *J. Cleaner Prod.*, vol. 350, p. 131500, 2022.
- [10] Y. Wang, Q. Yuan, S. Zhou, and L. Zhang, "Global spatiotemporal completion of daily high-resolution tcco from tropomi over land using a swath-based local ensemble learning method," *ISPRS J. Photogramm. Remote Sens.*, vol. 194, pp. 167–180, 2022.
- [11] S. Salcedo-Sanz, P. Ghamisi, M. Piles, M. Werner, L. Cuadra, A. Moreno-Martínez, E. Izquierdo-Verdiguier, J. Muñoz-Marí, A. Mosavi, and G. Camps-Valls, "Machine learning information fusion in earth observation: A comprehensive review of methods, applications and data sources," *Information Fusion*, vol. 63, pp. 256–272, 2020.
- [12] F. D. Van der Meer, H. M. Van der Werff, F. J. Van Ruitenbeek, C. A. Hecker, W. H. Bakker, M. D. Noomen, M. Van Der Meijde, E. J. M. Carranza, J. B. De Smeth, and T. Woldai, "Multi- and hyperspectral geologic remote sensing: A review," *Int. J. Appl. Earth Obs. Geoinf.*, vol. 14, no. 1, pp. 112–128, 2012.
- [13] Y. Wang, Q. Yuan, T. Li, L. Zhu, and L. Zhang, "Estimating daily full-coverage near surface o<sub>3</sub>, co, and no<sub>2</sub> concentrations at a high spatial resolution over china based on s5p-tropomi and geos-fp," *ISPRS J. Photogramm. Remote Sens.*, vol. 175, pp. 311–325, 2021.
- [14] M. Descour and E. Dereniak, "Computed-tomography imaging spectrometer: experimental calibration and reconstruction results," *Appl. Opt.*, vol. 34, no. 22, pp. 4817–4826, 1995.
- [15] H. Kwon and Y.-W. Tai, "Rgb-guided hyperspectral image upsampling," in *Proc. IEEE Int. Conf. Comput. Vis. (ICCV)*, 2015, pp. 307–315.
- [16] X. Cao, H. Du, X. Tong, Q. Dai, and S. Lin, "A prism-mask system for multispectral video acquisition," *IEEE Trans. Pattern. Anal. Mach. Intell.*, vol. 33, no. 12, pp. 2423–2435, 2011.
- [17] T. Akgun, Y. Altunbasak, and R. M. Mersereau, "Super-resolution reconstruction of hyperspectral images," *IEEE Trans. Image Process.*, vol. 14, no. 11, pp. 1860–1875, 2005.
- [18] S. Gou, S. Liu, S. Yang, and L. Jiao, "Remote sensing image super-resolution reconstruction based on nonlocal pairwise dictionaries and double regularization," *IEEE J. Sel. Top. Appl. Earth Obs. Remote Sens.*, vol. 7, no. 12, pp. 4784–4792, 2014.
- [19] R. Dian, T. Shan, W. He, and H. Liu, "Spectral super-resolution via model-guided cross-fusion network," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 35, no. 7, pp. 10059–10070, 2024.
- [20] Y. Wu, R. Dian, and S. Li, "Multistage spatial-spectral fusion network for spectral super-resolution," *IEEE Trans. Neural Netw. Learn. Syst.*, pp. 1–11, 2024.
- [21] J. Li, C. Wu, R. Song, Y. Li, W. Xie, L. He, and X. Gao, "Deep hybrid 2-d-3-d cnn based on dual second-order attention with camera spectral sensitivity prior for spectral super-resolution," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 34, no. 2, pp. 623–634, 2021.
- [22] J. He, J. Li, Q. Yuan, H. Shen, and L. Zhang, "Spectral response function-guided deep optimization-driven network for spectral super-resolution," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 33, no. 9, pp. 4213–4227, 2021.
- [23] J. Li, C. Wu, R. Song, Y. Li, and F. Liu, "Adaptive weighted attention network with camera spectral sensitivity prior for spectral reconstruction from rgb images," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW)*, 2020, pp. 462–463.
- [24] Y. Cai, J. Lin, Z. Lin, H. Wang, Y. Zhang, H. Pfister, R. Timofte, and L. Van Gool, "Mst++: Multi-stage spectral-wise transformer for efficient spectral reconstruction," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2022, pp. 745–755.
- [25] R. Dian, Y. Liu, and S. Li, "Spectral super-resolution via deep low-rank tensor representation," *IEEE Trans. Neural Netw. Learn. Syst.*, pp. 1–11, 2024.
- [26] J. Li, Y. Leng, R. Song, W. Liu, Y. Li, and Q. Du, "Mformer: Taming masked transformer for unsupervised spectral reconstruction," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, pp. 1–12, 2023.
- [27] —, "Mformer: Taming masked transformer for unsupervised spectral reconstruction," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, pp. 1–12, 2023.
- [28] K. C. Chan, X. Wang, K. Yu, C. Dong, and C. C. Loy, "Basicvsr: The search for essential components in video super-resolution and beyond," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2021, pp. 4947–4956.
- [29] Y. Xiao, Q. Yuan, K. Jiang, X. Jin, J. He, L. Zhang, and C.-W. Lin, "Local-global temporal difference learning for satellite video super-resolution," *IEEE Trans. Circuits Syst. Video Technol.*, vol. 34, no. 4, pp. 2789–2802, 2024.
- [30] Z. Liu, Y. Lin, Y. Cao, H. Hu, Y. Wei, Z. Zhang, S. Lin, and B. Guo, "Swin transformer: Hierarchical vision transformer using shifted windows," in *Proc. IEEE Int. Conf. Comput. Vis. (ICCV)*, 2021, pp. 10012–10022.
- [31] L. Zhu, B. Liao, Q. Zhang, X. Wang, W. Liu, and X. Wang, "Vision mamba: Efficient visual representation learning with bidirectional state space model," *arXiv preprint arXiv:2401.09417*, 2024.
- [32] S. Woo, J. Park, J.-Y. Lee, and I. S. Kweon, "Cbam: Convolutional block attention module," in *Proc. Eur. Conf. Comput. Vis. (ECCV)*, September 2018.
- [33] M. Breuer and J. Albertz, "Geometric correction of airborne whiskbroom scanner imagery using hybrid auxiliary data," *International Archives of Photogrammetry and Remote Sensing*, vol. 33, no. B3/1; PART 3, pp. 93–100, 2000.
- [34] D. Poli and T. Toutin, "Review of developments in geometric modelling for high resolution satellite pushbroom sensors," *Photogramm. Rec.*, vol. 27, no. 137, pp. 58–73, 2012.
- [35] X. Cao, T. Yue, X. Lin, S. Lin, X. Yuan, Q. Dai, L. Carin, and D. J. Brady, "Computational snapshot multispectral cameras: Toward dynamic

- capture of the spectral world," *IEEE Signal Process. Mag.*, vol. 33, no. 5, pp. 95–108, 2016.
- [36] H. Du, X. Tong, X. Cao, and S. Lin, "A prism-based system for multispectral video acquisition," in *Proc. IEEE Int. Conf. Comput. Vis. (ICCV)*. IEEE, 2009, pp. 175–182.
- [37] A. A. Wagadarikar, N. P. Pitsianis, X. Sun, and D. J. Brady, "Video rate spectral imaging using a coded aperture snapshot spectral imager," *Opt. Express*, vol. 17, no. 8, pp. 6368–6388, 2009.
- [38] Y. Cai, X. Hu, H. Wang, Y. Zhang, H. Pfister, and D. Wei, "Learning to generate realistic noisy images via pixel-level noise-aware adversarial training," *Adv. Neural Inf. Process. Syst.*, vol. 34, pp. 3259–3270, 2021.
- [39] Y. Cai, J. Lin, X. Hu, H. Wang, X. Yuan, Y. Zhang, R. Timofte, and L. Van Gool, "Mask-guided spectral-wise transformer for efficient hyperspectral image reconstruction," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2022, pp. 17 502–17 511.
- [40] X. Hu, Y. Cai, J. Lin, H. Wang, X. Yuan, Y. Zhang, R. Timofte, and L. Van Gool, "Hdnet: High-resolution dual-domain learning for spectral compressive imaging," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2022, pp. 17 542–17 551.
- [41] T. Huang, W. Dong, X. Yuan, J. Wu, and G. Shi, "Deep gaussian scale mixture prior for spectral compressive imaging," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2021, pp. 16 216–16 225.
- [42] Y. Cai, J. Lin, X. Hu, H. Wang, X. Yuan, Y. Zhang, R. Timofte, and L. Van Gool, "Coarse-to-fine sparse transformer for hyperspectral image reconstruction," in *Proc. Eur. Conf. Comput. Vis. (ECCV)*. Springer, 2022, pp. 686–704.
- [43] L. Wang, C. Sun, Y. Fu, M. H. Kim, and H. Huang, "Hyperspectral image reconstruction using a deep spatial-spectral prior," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2019, pp. 8032–8041.
- [44] Z. Meng, J. Ma, and X. Yuan, "End-to-end low cost compressive spectral imaging with spatial-spectral self-attention," in *Proc. Eur. Conf. Comput. Vis. (ECCV)*. Springer, 2020, pp. 187–204.
- [45] Z. Xiong, Z. Shi, H. Li, L. Wang, D. Liu, and F. Wu, "Hscnn: Cnn-based hyperspectral image recovery from spectrally undersampled projections," in *Proc. IEEE Int. Conf. Comput. Vis. Workshops (ICCVW)*. IEEE, 2017, pp. 518–525.
- [46] Z. Shi, C. Chen, Z. Xiong, D. Liu, and F. Wu, "Hscnn+: Advanced cnn-based hyperspectral recovery from rgb images," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW)*, 2018, pp. 1052–10528.
- [47] B. Arad, O. Ben-Shahar, R. Timofte, and S. Ghsal, "Ntire 2018 challenge on spectral reconstruction from rgb images," 2018, pp. 1042–104 209.
- [48] T. Stiebel, S. Koppers, P. Seltsam, and D. Merhof, "Reconstructing spectral images from rgb-images using a convolutional neural network," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW)*, June 2018.
- [49] A. Vaswani, "Attention is all you need," *Adv. Neural Inf. Process. Syst.*, vol. 30, pp. 1–9, 2017.
- [50] J. Hu, L. Shen, and G. Sun, "Squeeze-and-excitation networks," in *Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR)*, 2018, pp. 7132–7141.
- [51] S. Woo, J. Park, J.-Y. Lee, and I. S. Kweon, "Cbam: Convolutional block attention module," in *Proc. Eur. Conf. Comput. Vis. (ECCV)*, 2018, pp. 3–19.
- [52] H. Peng, X. Chen, and J. Zhao, "Residual pixel attention network for spectral reconstruction from rgb images," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW)*, June 2020.
- [53] A. Dosovitskiy, "An image is worth 16x16 words: Transformers for image recognition at scale," *arXiv preprint arXiv:2010.11929*, 2020.
- [54] Y. Cai, J. Lin, H. Wang, X. Yuan, H. Ding, Y. Zhang, R. Timofte, and L. V. Gool, "Degradation-aware unfolding half-shuffle transformer for spectral compressive imaging," *Adv. Neural Inf. Process. Syst.*, vol. 35, pp. 37 749–37 761, 2022.