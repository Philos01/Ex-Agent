

# Unsupervised Spectral Super-Resolution Guided by Spectral Sampling Priors

Xintao Zhong 

Image: ORCID icon

, Shenfu Zhang, Chenyang Lu 

Image: ORCID icon

, Xuejian Sun, Feng Shao 

Image: ORCID icon

, *Senior Member, IEEE*, Weiwei Sun 

Image: ORCID icon

, *Senior Member, IEEE*, and Xiangchao Meng 

Image: ORCID icon

, *Senior Member, IEEE*

**Abstract**—Spectral super-resolution (SSR) has garnered significant attention in recent years. Most existing networks rely on supervised methods, which require paired RGB and hyperspectral images (HSIs) for training. However, HSI acquisition is costly and time-consuming due to specialized hardware and complex preprocessing. In addition, spectral mixing phenomena in low-resolution HSIs degrade image quality. To address these challenges, spectral super-resolution (SSR) techniques have emerged to generate high-quality HSIs from widely accessible RGB images, enabling applications in agriculture, medicine, and environmental monitoring. To address these issues, we propose a novel unsupervised SSR network guided by spectral sampling priors (*SPointNet*). Inspired by multimodality text-image fusion techniques, we first introduce the point-image fusion module (PI-Fusion), which fuses sampled spectral data with RGB images. We then utilize spectral unmixing for super-resolution module to produce a coarse HSI, maximizing the exploitation of spectral information. Finally, we integrate a multistage shuffle-unshuffle transformer to fuse the coarse HSI with the RGB image, enhancing its spatial information. *SPointNet* can ensure continuity and consistency in both spectral and spatial dimensions in the generation of the refined HSI, which is validated on three publicly available datasets.

**Index Terms**—Attention mechanism, deep learning, hyperspectral image (HSI), spectral super-resolution (SSR).

## I. INTRODUCTION

**H**YPERSPECTRAL image (HSI), characterized by its continuous narrowband spectrum and rich spectral information, holds significant value in fields, such as agriculture, medicine, food inspection, and environmental monitoring. However, three critical challenges hinder its application: 1) High

equipment costs limit the widespread deployment of hyperspectral sensors. 2) Complex preprocessing procedures impede practical implementation. 3) Spectral mixing effects in low-resolution HSIs reduce material identification accuracy. These limitations have driven researchers to adopt spectral super-resolution (SSR) techniques that reconstruct high-quality HSIs from RGB inputs. Compared to traditional HSI systems, RGB images offer advantages in acquisition cost and processing maturity, while HSIs demonstrate superior performance in a wide range of image processing tasks [1], [2], [3], [4], [5], [6], [7], including image classification [8], [9], [10], [11], target detection [12], [13], [14], [15]. Therefore, recent research has focused on developing SSR algorithms that establish mapping relationships between RGB and HSI data. This approach not only preserves the spectral advantages of HSI, but also effectively addresses the technical limitations of conventional systems, making it a key research area in image processing. Many existing approaches rely on techniques such as spectral basis functions [16], sparse dictionaries [17], maximum a posteriori (MAP) methods [18], [19], and more recently, deep learning models [20], [21], [22], [23], [24], [25], [26], [27].

Although deep learning is becoming increasingly popular in the field of SSR, several notable challenges remain. *First*, paired RGB and HSI data are difficult to obtain, since the cost of accessing HSI is expensive. *Second*, the conventional preprocessing of HSI is complicated, which involves radiometric calibration, atmospheric correction, geometric correction, and noise suppression. *In addition*, complex spectral mixing phenomena can lead to decreased image quality, especially in low spectral resolution scenarios. To address these challenges, some researchers have shifted their focus to unsupervised SSR tasks [28], [29], [30], which do not require paired RGB and HSI data and can simultaneously generate high-quality HSIs, demonstrating great potential for improving image quality and advancing technological applications.

Despite the recent advances in the unsupervised SSR task, the following issues still exist. 1) As shown in Fig. 1(a), existing SSR priors typically take the entire image as input, which introduces redundant information and thus reduces the efficiency of the super-resolution process. 2) Most SSR methods focus on improving the accuracy of spectral details in the reconstructed image but often overlook the loss of spatial information, which diminishes the overall quality of the final reconstruction.

To address the aforementioned challenges, we introduce a new network designed for the *unsupervised* SSR task. Our

Received 9 May 2025; revised 16 June 2025; accepted 24 July 2025. Date of publication 29 July 2025; date of current version 15 August 2025. This work was supported in part by the Zhejiang Provincial Natural Science Foundation of China under Grant LR23D010001, in part by the Project National Key R&D Program of China under Grant 2024YFF1400900, in part by the National Natural Science Foundation of China under Grant 42171326, and in part by the Ningbo Natural Science Foundation under Grant 2022J076. (Corresponding author: Xiangchao Meng.)

Xintao Zhong, Shenfu Zhang, Chenyang Lu, Feng Shao, and Xiangchao Meng are with the Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo 315211, China (e-mail: 2311100200@nbu.edu.cn; zhang-shenfu\_nb@163.com; luchenyang1@nbu.edu.cn; shaofeng@nbu.edu.cn; mengxiangchao@nbu.edu.cn).

Xuejian Sun is with the Aerospace Information Research Institute, Chinese Academy of Sciences, Beijing 100094, China (e-mail: sunxj201494@aircas.ac.cn).

Weiwei Sun is with the Department of Geography and Spatial Information Techniques, Ningbo University, Ningbo 315211, China (e-mail: sunweiwei@nbu.edu.cn).

Digital Object Identifier 10.1109/JSTARS.2025.3593668

![Figure 1: (a) Current unsupervised SSR tasks that utilize the entire image as prior input. (b) The network proposed in this article employing a point-spectral prior as input, which avoids introducing redundant information to the SSR network.](aa9e46d6f962be5cebcbb5c654c9b13e_img.jpg)

Figure 1 consists of two diagrams, (a) and (b), illustrating different approaches to hyperspectral super-resolution (SSR).  
 Diagram (a) shows a flow where a 'Guided HSI' (Hyperspectral Image) is processed through 'Priors processing' to generate a 'Spectral Super-Resolution network'. This network takes an 'RGB' image as input and produces an 'HSI' output. The 'Guided HSI' is represented by a dashed box, indicating it is an external prior.  
 Diagram (b) shows a flow where an 'RGB' image and a 'point-spectral prior' (represented by a stack of N pixels) are both input into a 'Spectral Super-Resolution network'. The network produces an 'HSI' output. The 'point-spectral prior' is represented by a dashed box, indicating it is an input to the network.

Figure 1: (a) Current unsupervised SSR tasks that utilize the entire image as prior input. (b) The network proposed in this article employing a point-spectral prior as input, which avoids introducing redundant information to the SSR network.

Fig. 1. (a) Represents the current unsupervised SSR tasks that utilize the entire image as prior input. (b) Refers to the network proposed in this article employing a point-spectral prior as input, which avoids introducing redundant information to the SSR network.

network consists of the point-image fusion module (PI-Fusion), spectral unmixing for super-resolution module (UMSR), and multistage shuffle-unshuffle transformer (MSUT). As shown in Fig. 1(b), in the *PI-Fusion* module, we are the first to replace the traditional full-image input with *point-spectral priors*, which ensures more precise spectral information injection while reducing redundant data. Drawing from classical text-image fusion methods [31], point-spectral priors and RGB images are independently processed to generate feature representations of the same dimension. In the *UMSR* module, we employ a spectral unmixing-based method that effectively extracts and enhances the spectral information embedded within the fused features, improving both the clarity and precision of the spectral characteristics. By isolating the spectral components, this method allows us to obtain purer and more detailed spectral signatures. However, the resulting coarse HSI, while rich in spectral information, suffers from low spatial resolution. To compensate for this, the *MSUT* module fuses the high spatial information of RGB images with the spectral details of the coarse HSI. This fusion process generates a final output that maintains both detailed spectral information and superior spatial resolution. Specifically, we implement the MSUT module based on the swin transformer, a vision transformer (ViT) variant that captures long-range dependencies through shifted window attention, enabling effective spatial-spectral feature integration.

The main contributions of our work can be summarized as follows.

- 1) We propose a novel unsupervised network for RGB super-resolution. It is the first unsupervised SSR network that utilizes spectral point data as priors, which avoids redundant information and better matches the spectral characteristics.
- 2) We propose three novel modules, namely PI-Fusion, UMSR, and MSUT. PI-Fusion and UMSR can more accurately provide the spectral information needed for RGB

super-resolution. MSUT is proposed to compensate for the loss of spatial information during the super-resolution process.

- 3) Through extensive experiments on three publicly available datasets, our network exhibits state-of-the-art performance compared to other methods.

## II. RELATED WORK

**HSI Acquisition:** In hyperspectral imaging, three common acquisition methods include pushbroom, whiskbroom, and wavelength scanning. Pushbroom imaging captures continuous lines of data by moving, making it suitable for applications such as remote sensing and environmental monitoring [32], [33]. Whiskbroom imaging collects data point by point and is typically used for materials analysis in laboratory settings. Wavelength scanning, on the other hand, obtains spectral information by varying the wavelength of light, which is widely applied in medical imaging and agriculture. To address the limitations of traditional spectrometers in terms of acquisition speed and efficiency, snapshot compressive imaging (SCI) has emerged [34], [35], [36], [37], allowing for simultaneous capture of spatial and spectral information, significantly enhancing acquisition speed and particularly suited for dynamic scenes such as monitoring and real-time observation. However, SCI also has the drawback of high costs, primarily associated with complex optical components and specialized sensors, which limits its widespread adoption in certain applications. Despite its advantages in efficiency, a heavy investment is required for its broader usage. Therefore, the SSR task has significant research and practical value.

**Deep learning-Base Spectral Unmixing:** Recent advancements in spectral unmixing have witnessed the integration of physically interpretable deep learning frameworks. These methods synergize classical linear mixing models (LMM) with neural networks to enhance feature representation while maintaining physical constraints. Guo et al. [38] pioneered the incorporation of subpixel spectral unmixing into change detection tasks, leveraging endmember-abundance decomposition to strengthen temporal correspondence. Zou et al. [39] proposed a dual-branch residual network with alternating optimization of endmember/abundance matrices, explicitly embedding nonnegativity and sum-to-one constraints through an iterative refinement mechanism that addresses the physical modeling gap in deep models. In hyperspectral super-resolution applications, Su et al. [40] introduced a cross-modal autoencoder with parameter sharing between low-resolution HS and high-resolution MS data, enabling coherent abundance estimation across modalities. To mitigate reliance on pure pixels, Hong et al. [41] developed EGU-Net with a two-stream encoder architecture, employing parameter sharing for joint end member-abundance estimation and introducing a pure-pixel guided attention module for improved mixed pixel decomposition. Addressing spectral-spatial information imbalance, Zhao et al. [42] incorporated LSTM networks into an asymmetric autoencoder, using temporal modeling to enforce spectral continuity while spatial attention compensates for HSIs' limited spatial resolution. These advancements

demonstrate the evolving synergy between physical modeling and deep learning in spectral unmixing, particularly in addressing mixed pixel decomposition and spectral-spatial information fusion, thereby establishing crucial theoretical foundations for our point-based spectral sampling paradigm.

*ViTs:* Transformers have seen significant advancements in recent years, especially with the introduction of ViTs in image processing. Concurrently, they are widely applied in various image-related tasks, including image classification [43], [44], [45], object detection [46], [47], [48], semantic segmentation [49], [50], [51], [52], and image super-resolution [53], [54], [55]. The underlying rationale behind this widespread application stems from their exceptional capability to encompass a vast receptive field and meticulously capture intricate long-range dependencies within image data. For example, Cai et al. [56] were the first to propose using transformers for HSI reconstruction. Cai et al. [57] combined the sparsity of HSI with transformers to progressively reconstruct HSI from coarse to fine. Li et al. [30] proposed a dual-spectral line multihead self-attention mechanism to reconstruct HSI.

*SSR for RGB:* SSR can be broadly divided into two series, namely traditional approaches and deep learning approaches (both supervised and unsupervised). Traditional methods, such as creating sparse dictionaries of hyperspectral signatures and their corresponding RGB projections, have been widely used. For example, Arad and Ben-Shahar [58] developed a sparse dictionary using hyperspectral priors, while Gao et al. [59] tackled SSR by jointly learning low-rank dictionaries for HSI and multispectral images (MSIs). Supervised deep learning methods have also seen significant advancements. Zhang et al. [60] used transformers to capture long-range dependencies, while Shi et al. [61] employed dense and residual connections to enhance performance. Cai et al. [62] used multihead self-attention in the spectral dimension for progressive reconstruction, and Zhao et al. [63] applied PixelShuffle layers for interlevel interactions and artifact removal. Chen et al. [64] proposed a spectral-cascaded diffusion model, which employs a coarse-to-fine strategy with progressive spectral refinement and dynamic truncation to improve SSR performance. Zhou et al. [65] introduced a selective semantic transformer (SST) that models both intra- and intersuperpixel spectral-spatial relations for more interpretable and accurate SSR. However, supervised methods rely on paired RGB and HSI data, which are difficult to obtain in practice. This leads to the rise of unsupervised approaches. For instance, Qu et al. [55] used spectral and spatial priors, Zhu et al. [29] applied semantic information and adversarial learning, and Li et al. [30] introduced a dual-spectral multihead attention mechanism for high-resolution HSI reconstruction. Recent unsupervised MSI-HSI fusion studies have offered new insights for SSR by enabling cross-modal feature fusion and deep prior mining to enhance reconstruction performance. Li et al. [66] proposed EDIP-Net, a two-stage framework that generates scene-relevant coarse estimates via zero-shot learning to guide deep networks, combining dual U-shaped architectures and degradation-aware decision fusion to preserve spectral details and spatial consistency. Cao et al. [67] designed UMSFT, a multilevel spatio-spectral fusion transformer that

hierarchically integrates multiscale features using spatial fusion modules and spectral cross-attention, strengthening long-range spectral-spatial dependency modeling. For blind fusion scenarios, Cao et al. [68] further introduced uHNTC, which achieves deep cross-modal interaction under unknown degradations via adaptive degradation subnets and transformer-based cross-feature attention, mitigating spectral distortion, and spatial blurring. These methods, through innovations in prior injection, cross-modal attention, and degradation modeling, advance unsupervised SSR from single spectral enhancement to “spectral-spatial collaborative optimization,” providing effective solutions for resolution improvement in complex scenes. However, the above methods pay little attention to the preservation of spatial information during the super-resolution process and introduce redundant information when incorporating priors.

## III. METHODOLOGY

This section first defines the problem in Section II-A. Afterward, the framework is proposed in Section II-B, with three novel components (PI-Fusion, UMSR, and MSUT) detailed in Section III-C, Section III-D, and Section III-E, respectively.

### A. Problem Definition

SPointNet primarily achieves SSR through spectral unmixing. Therefore, we provide definitions for spectral unmixing and SSR.

1) *Spectral Unmixing:* HSI typically has a lower spatial resolution, which means that each pixel generally contains multiple different materials, leading to the mixed-pixel problem in hyperspectral imaging. Spectral unmixing seeks to decompose each pixel into a collection of pure spectral signatures (endmembers) and their associated proportions (abundances).

Assume  $\mathbf{Z} \in \mathbb{R}^{H \times W \times C}$  is an HSI with  $C$  spectral channels and  $H \times W$  spatial pixels. Let  $\mathbf{M} \in \mathbb{R}^{p \times C}$  be the endmember matrix containing  $p$  pure spectra, and  $\mathbf{A} = (a_{i,j})_{H \times W \times p} \in \mathbb{R}^{H \times W \times p}$  represent the abundance matrix. According to the LMM, the unmixing module can be represented as

$$\mathbf{Z} = R_2(R_1(\mathbf{A}) \cdot \mathbf{M}) + \mathbf{N} \quad (1)$$

where  $\mathbf{N}$  denotes an additive white Gaussian noise matrix.  $R_1$  represents the reshape operation, which reshapes the  $\mathbb{R}^{H \times W \times p}$  to  $\mathbb{R}^{HW \times p}$ ,  $R_2$  represents the reshape operation which reshapes the  $\mathbb{R}^{HW \times C}$  to  $\mathbb{R}^{H \times W \times C}$ . In addition, the abundance matrix must comply with the non-negativity constraint (ANC) and the sum-to-one constraint (ASC), as expressed by

$$\sum_{i=1}^p a_{i,j} = 1 \quad \forall i \quad (2)$$

$$a_{i,j} \geq 0 \quad \forall i, \forall j. \quad (3)$$

2) *SSR:* In the context of SSR, assume that we have an HSI denoted by  $\mathbf{Z} \in \mathbb{R}^{H \times W \times C}$ , along with a spectral response function  $R$ . Using this function, the RGB image  $\mathbf{X} \in \mathbb{R}^{H \times W \times 3}$  can be

![Figure 2: Illustration of the proposed SPointNet architecture. The diagram shows three main components: PI-Fusion, UMSR, and MSUT. PI-Fusion takes 'Sample Data' (represented by colored bars) and an 'RGB' image as input, processing them through 'Fusion Attention' to produce 'Abundance Maps'. A loss function L_KL is shown between the abundance maps and 'Endmembers' (represented by a line graph). UMSR takes the 'Abundance Maps' and a 'Coarse-HSI' image to produce an 'HRHSI' (High Resolution Hyperspectral Image). A loss function L_TV is shown between the HRHSI and the Coarse-HSI. MSUT takes the 'HRHSI' and the 'RGB' image as input, processing them through three 'SWMS' (Shifted Window Multi-Head Self-Attention) blocks with 'Pixel Shuffle' and 'Pixel Unshuffle' operations to produce the final output. A legend on the right shows the symbols for 'Conv 3x3' (blue square), 'Relu' (white square), 'Maxpool' (green square), 'Linear' (yellow square), and 'Softmax' (orange square).](9e6062272bbe3ddbb7c0606721d64cf0_img.jpg)

Figure 2: Illustration of the proposed SPointNet architecture. The diagram shows three main components: PI-Fusion, UMSR, and MSUT. PI-Fusion takes 'Sample Data' (represented by colored bars) and an 'RGB' image as input, processing them through 'Fusion Attention' to produce 'Abundance Maps'. A loss function L\_KL is shown between the abundance maps and 'Endmembers' (represented by a line graph). UMSR takes the 'Abundance Maps' and a 'Coarse-HSI' image to produce an 'HRHSI' (High Resolution Hyperspectral Image). A loss function L\_TV is shown between the HRHSI and the Coarse-HSI. MSUT takes the 'HRHSI' and the 'RGB' image as input, processing them through three 'SWMS' (Shifted Window Multi-Head Self-Attention) blocks with 'Pixel Shuffle' and 'Pixel Unshuffle' operations to produce the final output. A legend on the right shows the symbols for 'Conv 3x3' (blue square), 'Relu' (white square), 'Maxpool' (green square), 'Linear' (yellow square), and 'Softmax' (orange square).

Fig. 2. Illustration of our proposed SPointNet. The network consists of three components, namely PI-Fusion, UMSR, and MSUT. First, PI-Fusion is applied to fuse the sampled data (point-spectral priors) with RGB images. Second, the UMSR module performs initial super-resolution on the fused feature. Finally, the MSUT module fuses the initially super-resolved image with the RGB image.

obtained through the following relationship:

$$\mathbf{X} = R_4(R_3(\mathbf{Z}) \cdot \mathbf{r}) + \mathbf{N} \quad (4)$$

where  $R_3$  represents the reshape operation, which reshapes the  $\mathbb{R}^{H \times W \times C}$  to  $\mathbb{R}^{HW \times C}$ ,  $R_4$  represents the reshape operation which reshapes the  $\mathbb{R}^{HW \times 3}$  to  $\mathbb{R}^{H \times W \times 3}$ .

The SSR task involves estimating the HR-HSI from the RGB image, which can be represented as follows:

$$\mathbf{Z} = f(\mathbf{X}; \theta) \quad (5)$$

where  $f$  is the module used for SSR, and  $\theta$  comprises the module parameters.

### B. Our Architecture

The overall framework of the network is shown in Fig. 2. First, we used the clustering of  $k$ -means and calculations of spectral similarity to sample point-spectral  $\mathbf{s} \in \mathbb{R}^{p \times C}$  from the guided HSI, ensuring better RGB-matched spectral information with minimal redundant information. Second, the input RGB image  $\mathbf{X} \in \mathbb{R}^{H \times W \times 3}$  is fused with the point-spectral  $\mathbf{S}$  through PI-Fusion, embedding the spectral information needed for super-resolution, and then passed through UMSR to generate a coarse HSI  $\hat{\mathbf{Z}} \in \mathbb{R}^{H \times W \times C}$ . Subsequently, in MSUT, the generated coarse HSI  $\hat{\mathbf{Z}}$  is further fused with the RGB image  $\mathbf{X}$  using Pixel shuffle and unshuffle (PSU) method and three swin transformers without masking and shifted window (SWMS) blocks to produce the final HSI  $\mathbf{Z} \in \mathbb{R}^{H \times W \times C}$  with high spatial and spectral resolution, effectively overcoming the spatial information deficiency in SSR methods.

### C. PI-Fusion

In PI-Fusion, we introduce a novel method for RGB SSR by leveraging point-spectral priors, which guide the process. Specifically, the prior  $\mathbf{s}$  is derived from the guided HSI by applying  $K$ -means clustering to partition the HSI into  $n$

distinct regions based on their spectral characteristics. Within each region, we perform a global average pooling operation on the pixels, resulting in a sequence  $k$  that represents the average spectral signature of that region.

To further refine the prior, we compute the spectral angle between the sequence  $k$  and the spectral signatures of all pixels within the same cluster. The pixel whose spectral signature has the smallest spectral angle with  $k$  is considered the most representative of that cluster. This procedure allows us to extract a set of  $n$  pixels from the guided HSI, which serves as the point-spectral prior  $\mathbf{s} \in \mathbb{R}^{n \times C}$ , where  $n$  is the number of RGB endmembers and  $C$  is the number of spectral bands. By using this point-spectral prior, we effectively enhance the accuracy of spectral information in the RGB domain while also reducing the redundancy typically present in the data.

$$\mathbf{s}_k = \arg \min_{\text{sam}} (K_k(\mathbf{Y}_g), \text{GAP}(K_k(\mathbf{Y}_g))), 1 \leq k \leq n \quad (6)$$

$$\mathbf{s} = \text{Concat}(\mathbf{s}_1, \mathbf{s}_2, \dots, \mathbf{s}_n). \quad (7)$$

where  $\mathbf{Y}_g \in \mathbb{R}^{H \times W \times C}$  represents the guided HSI,  $\text{GAP}()$  denotes global average pooling,  $K_n()$  represents the pixel area of the  $n$ th class after the  $K$ -means operation,  $\arg \min_{\text{sam}}()$  calculates the spectral angle loss for each pixel pair and returns the pixel with the smallest loss. The operation is illustrated in Fig. 3.

Building upon the integration of text and image data [31], we propose an analogous approach to treat the spectral prior  $\mathbf{s}$  in a similar manner as text data. To achieve this, we transform both the prior  $\mathbf{s}$  and the RGB image  $\mathbf{X}$  into one-dimensional representations and utilize self attention to model their complex interactions effectively. To model the interactions between the spectral prior and the RGB image, we employ a fusion-based attention mechanism. Specifically, the spectral prior  $\mathbf{s}$  and RGB image  $\mathbf{X}$  are first encoded into one-dimensional feature vectors  $\mathbf{F}_p$  and  $\mathbf{F}_{\text{RGB}}$ , respectively. These features are then concatenated and fed into a multihead self-attention module, referred to as

![Figure 3: Point-spectral prior method diagram. An input image is processed by K-means clustering to produce 'n classes' (a scatter plot of colored points). This is followed by 'n*Cluster GAP' and 'n*SAM_min' blocks. The output is 'n pixels' (represented by colored vertical bars), which are then processed by a 'net' block.](e394c2b5c61344f6a12397f430086072_img.jpg)

Figure 3: Point-spectral prior method diagram. An input image is processed by K-means clustering to produce 'n classes' (a scatter plot of colored points). This is followed by 'n\*Cluster GAP' and 'n\*SAM\_min' blocks. The output is 'n pixels' (represented by colored vertical bars), which are then processed by a 'net' block.

Fig. 3. Figure above illustrates our point-spectral prior method. Our method injects more precise spectral information than previous methods, which may introduce redundant information.

![Figure 4: (a) Illustration of fusion attention block. (b) Illustration of SWMS block. Both diagrams show a sequence of layers: Input, Input Embedding, MSA/W-MSA, Add & Norm, Linear/MLP, Add & Norm, and Output. (a) shows a standard attention block with MSA. (b) shows the SWMS block with W-MSA and a skip connection bypassing the W-MSA layer.](53f1f7d17b3e7aae62169c41d2a88a77_img.jpg)

Figure 4: (a) Illustration of fusion attention block. (b) Illustration of SWMS block. Both diagrams show a sequence of layers: Input, Input Embedding, MSA/W-MSA, Add & Norm, Linear/MLP, Add & Norm, and Output. (a) shows a standard attention block with MSA. (b) shows the SWMS block with W-MSA and a skip connection bypassing the W-MSA layer.

Fig. 4. (a) Illustration of fusion attention block. (b) Illustration of SWMS block.

fusion-attention, where their joint representation is optimized in a shared space to dynamically learn interactions between spectral and spatial cues during fusion.

The structure of the self attention mechanism is depicted in Fig. 4(a). In this process, the prior  $\mathbf{S}$  is passed through two linear layers and a ReLU activation layer to transform it into a one-dimensional vector. This transformation allows the spectral prior to be processed as a sequence, making it compatible with the image representation. Similarly, the RGB image  $\mathbf{X}$  undergoes a series of operations to convert it into a one-dimensional vector: it first passes through two CRM (Convolution, ReLU, and Max-Pooling) layers, followed by a final linear layer. These operations are designed to capture the spatial and spectral features of the RGB image before it is transformed into a vector form.

The entire process is formalized as follows: the spectral prior  $\mathbf{s}$  and RGB image  $\mathbf{X}$  are first projected into one-dimensional feature vectors  $\mathbf{F}_p$  and  $\mathbf{F}_{\text{RGB}}$ , respectively. These features are then concatenated and fed into the cross-attention mechanism, where their joint representation is optimized in a shared space to dynamically learn interactions between spectral and spatial cues during fusion.

$$\mathbf{F}_p = M_l(M_r(M_l(\mathbf{s}))) \quad (8)$$

$$\mathbf{F}_{\text{RGB}} = M_{\text{CMR}}(M_l(\mathbf{X})) \quad (9)$$

$$\mathbf{F}_{\text{concat}} = \text{Concat}(\mathbf{F}_p, \mathbf{F}_{\text{RGB}}) \quad (10)$$

$$\mathbf{F}_{\text{Attention}} = M_A(\mathbf{F}_{\text{concat}}). \quad (11)$$

In the formula,  $M_l$ ,  $M_r$ , and  $M_{\text{CMR}}$  denote linear, ReLU, and CMR modules, respectively, where the CMR module includes convolution, ReLU, and max-pooling. Cross attention is represented as  $M_A$ .  $\mathbf{F}_p$  and  $\mathbf{F}_{\text{RGB}}$  are one-dimensional feature vectors derived from the spectral prior  $\mathbf{s}$  and the RGB image  $\mathbf{X}$ , respectively, and are concatenated into  $\mathbf{F}_{\text{concat}}$ . The output feature map after their interaction is  $\mathbf{F}_{\text{Attention}} \in \mathbb{R}^{H \times W \times C}$ .

### D. UMSR

The UMSR module utilizes an auto-encoder-based unmixing architecture to separate the feature map  $\mathbf{F}_{\text{Attention}}$  into the abundance and the endmember. This approach is crucial for enhancing spatial representation, which is key in tasks such as RGB-to-HSI super-resolution, where both spectral and spatial fidelity are needed. The encoder's primary function is to unmix  $\mathbf{F}_{\text{Attention}}$  into abundance maps  $\mathbf{A} \in \mathbb{R}^{H \times W \times p}$ , where  $H$  and  $W$  represent the spatial dimensions of the input image, and  $p$  denotes the number of endmembers. To ensure the physical validity of the abundance maps, the final layer of the encoder applies a Softmax activation function, enforcing both the additive non-negativity constraint (ANC) and the abundance sum constraint (ASC) on the generated maps. These constraints ensure that the abundance maps are both physically plausible and consistent with the inherent properties of spectral unmixing.

The decoder then utilizes the abundance maps  $\mathbf{A}$  as input to reconstruct the feature map  $\mathbf{F}_{\text{Attention}}$  into a coarse HSI  $\hat{\mathbf{Z}}$ . The decoder's parameters act as the endmember matrix  $\mathbb{R}^{p \times C}$ , where  $C$  represents the number of spectral bands in the HSI. This reconstruction process facilitates the super-resolution of  $\mathbf{F}_{\text{Attention}}$ , improving its spectral resolution while preserving spatial information. The role of the decoder is particularly important in maintaining spatial consistency, ensuring that the feature map  $\mathbf{F}_{\text{Attention}}$  is accurately translated into the higher-resolution HSI.

Within the UMSR block, the input image first passes through an encoder comprising four linear layers. These layers progressively extract relevant information, effectively distilling the spatial and spectral features of the image. A Softmax function is applied after the encoder's output to enforce the physical constraints on the abundance maps. This helps maintain the physical integrity of the abundance maps, which is essential for accurate spectral unmixing. The encoder maps the input image to a latent representation  $\mathbf{A}$ , which is passed to the decoder. The decoder then reconstructs the latent representation into the coarse HSI  $\hat{\mathbf{Z}}$ , which serves as the foundation for subsequent refinement. The following formula formalizes the operation of

the UMSR block:

$$\mathbf{A} = M_{l1}(\dots M_{l4}(M_s(\mathbf{F}_{\text{Attention}})))) \quad (12)$$

$$\hat{\mathbf{Z}} = M_l(\mathbf{A}) \quad (13)$$

where  $M_s$  represents the Softmax layer.

As each pixel generally contains only a limited number of pure spectra, the abundance map  $\mathbf{A}$  is expected to be sparse. To enforce this sparsity, we adopt a sparsity loss based on the Kullback–Leibler (KL) divergence between the abundance map  $\mathbf{A}$  and a small constant  $\epsilon$ , which serves as the mean of the desired sparse distribution. The KL divergence is a well-established measure of how one probability distribution diverges from a second, reference probability distribution. In this context, it quantifies the difference between the actual abundance map and a distribution with a tiny constant  $\epsilon$  as the mean.

$$\begin{aligned} \mathcal{L}_{KL} &= \sum_{j=1}^{HW} \text{KL}(\epsilon \| \mathbf{A}_j) \\ &= \sum_{j=1}^{HW} \left( \epsilon \log \frac{\epsilon}{\mathbf{A}_j} + (1 - \epsilon) \log \frac{1 - \epsilon}{1 - \mathbf{A}_j} \right). \end{aligned} \quad (14)$$

### E. MSUT

The Swin Transformer effectively retains the global attention capabilities of ViTs while reducing computational complexity through its windowed self-attention mechanism. However, the use of shifted windows and associated masking strategies disrupts interactions between boundary pixels, which weakens the model’s ability to capture long-range dependencies and results in degraded edge information preservation [69]. To address this limitation, we propose the SWMS architecture within the MSUT framework, as illustrated in Fig. 4(b). Instead of relying on shifted windows for cross-window interaction, the SWMS module removes both the masking mechanism and window-shifting strategy. Instead, it incorporates the pixel shuffling unit (PSU), which dynamically rearranges image rows and columns across network layers. As shown in Fig. 5, this operation enables more effective global attention modeling by allowing features from distant regions to interact, while also preserving critical boundary information that is typically lost in conventional window-based attention designs. By alternating between shuffle and unshuffle operations, the PSU facilitates multiscale feature learning and enhances spatial coherence, ultimately improving both spectral and spatial reconstruction quality in the SSR task.

The MSUT architecture consists of three SWMS modules, with the PSU operation integrated between them. The modules utilize window sizes of 8, 4, and 2, respectively, enabling hierarchical feature extraction. This structure functions similarly to a feature pyramid, enhancing the model’s ability to extract spatial information at multiple scales. As a result, it generates high-resolution HSI with both high spatial and spectral accuracy, preserving fine details in both dimensions.

This approach directly addresses the issues associated with the original Swin Transformer, ensuring that boundary information is retained and self-attention is efficiently computed across the

![Figure 5: The proposed PSU operation. The diagram shows two examples of pixel shuffling. In the top example, a 4x4 grid of image patches from 'Layer 1' is shuffled horizontally and vertically to form a new 4x4 grid in 'Layer 1+1'. In the bottom example, a 4x4 grid from 'Layer 1' is unshuffled back to its original arrangement in 'Layer 1+1'. Arrows labeled 'Shuffle' and 'Unshuffle' indicate the direction of the operation. Small circular icons with symbols are shown next to the rows and columns to illustrate the rearrangement pattern.](68ca7669d38a3c31f5a2c3a06fa802e3_img.jpg)

Figure 5: The proposed PSU operation. The diagram shows two examples of pixel shuffling. In the top example, a 4x4 grid of image patches from 'Layer 1' is shuffled horizontally and vertically to form a new 4x4 grid in 'Layer 1+1'. In the bottom example, a 4x4 grid from 'Layer 1' is unshuffled back to its original arrangement in 'Layer 1+1'. Arrows labeled 'Shuffle' and 'Unshuffle' indicate the direction of the operation. Small circular icons with symbols are shown next to the rows and columns to illustrate the rearrangement pattern.

Fig. 5. The proposed PSU operation. Shuffle rearranges pixels via horizontal and vertical transformations, while unshuffle restores the original arrangement by reversing this sequence.

entire image. The detailed process is described by the following formula:

$$\mathbf{F}_1 = \mathcal{F}_{\text{Shuffle}}(\text{SWMS}_8(\text{Concat}(\mathbf{X}, \hat{\mathbf{Z}}))) \quad (15)$$

$$\mathbf{F}_2 = \mathcal{F}_{\text{Unshuffle}}(\text{SWMS}_4(\mathbf{F}_1)) \quad (16)$$

$$\mathbf{Z} = \text{SWMS}_2(\mathbf{F}_2) \quad (17)$$

where  $\mathbf{F}_1 \in \mathbb{R}^{H \times W \times C}$  and  $\mathbf{F}_2 \in \mathbb{R}^{H \times W \times C}$  represent the feature maps at intermediate stages,  $\mathcal{F}_{\text{Shuffle}}$  and  $\mathcal{F}_{\text{Unshuffle}}$  are the two steps of the PSU,  $\text{SWMS}_w$  indicates the SWMS with  $w$  window size, and  $\mathbf{Z}$  is the final output.

For the final output  $\mathbf{Z}$  in MSUT, we define two loss functions: the reconstruction loss  $\mathcal{L}_R$  and the TV loss  $\mathcal{L}_{\text{TV}}$ . Since the HSI  $\mathbf{Z}$  is super-resolved from the RGB image  $\mathbf{X}$ , the RGB image  $\mathbf{X}$ , generated from  $\mathbf{Z}$  using the spectral response function, should ideally match the original  $\mathbf{X}$ . To minimize the difference between  $\mathbf{X}$  and  $\mathbf{Z} \cdot \mathbf{R}$ , we employ the  $L_2$  loss, as expressed in the following formula:

$$\mathcal{L}_R = \|\mathbf{X} - \mathbf{Z} \cdot \mathbf{R}\|_2 \quad (18)$$

Due to the physical characteristics of HSI, adjacent bands are similar to each other. Based on this property, we use TV loss  $\mathcal{L}_{\text{TV}}$  to enforce this physical characteristic. The TV loss is defined as

$$\mathcal{L}_{\text{TV}} = \sum_{i=1}^{HW} \sum_{j=1}^{C-1} (\mathbf{Z}_{i,j} - \mathbf{Z}_{i,j+1}). \quad (19)$$

Then, the total loss of the SPointNet is defined as follows:

$$\mathcal{L}_{\text{total}} = \alpha \mathcal{L}_R + \beta \mathcal{L}_{\text{TV}} + \gamma \mathcal{L}_{KL} \quad (20)$$

where  $\alpha$ ,  $\beta$ , and  $\gamma$  are tradeoff weights.

## IV. EXPERIMENTS

### A. Datasets

In our experiments, we utilize three distinct datasets, each chosen for its relevance to the task of SSR. *ICVL Dataset*: This dataset contains 201 images, each with 31 spectral channels. For the purpose of our experiments, we randomly selected 184 images to form the training set and 6 images for the test set. Before processing, each image was cropped to a size of  $31 \times 256 \times 256$ , ensuring consistent input dimensions across all images. *DFC2018 Houston Dataset*: This dataset consists of 50 spectral channels. In this experiment, we randomly selected 92 images to serve as the training set, while 6 images were reserved for the test set. The images are particularly useful for evaluating the performance of SSR on high-dimensional hyperspectral data. *TG1HRSSC Dataset*: This dataset includes three types of images: panchromatic images, visible near-infrared images with 54 effective spectral bands, and short-wave infrared images with 52 effective spectral bands. For our experiments, we focused on the visible near-infrared images, selecting 40 images as the training set and 6 images for the test set. This dataset offers a diverse range of spectral information, making it ideal for testing the robustness and effectiveness of the proposed method in handling different types of hyperspectral data.

### B. Experimental Settings

*Obtaining Point Spectral Prior*: For the ICVL, DFC2018 Houston, and TG1HRSSC datasets, the guided HSIs employed for deriving point-spectral priors are uniformly sourced from the Salinas dataset, which originates from the Salinas Valley in California, USA. This dataset comprises 204 spectral channels spanning the 0.4–2.5  $\mu\text{m}$  spectral range. Prior to experimental implementation, the guided HSI underwent spectral downsampling to align its channel count with that of the spectrally super-resolved RGB image. Concurrently, its spatial dimensions were reduced to  $256 \times 256$  to ensure spatial resolution consistency with the RGB input. These preprocessing steps ensure the input data are compatible with the model's requirements, thereby enabling precise fusion of spectral and spatial information while maintaining consistency in the spectral prior extraction pipeline and facilitating a rigorous cross-dataset performance evaluation of the proposed method.

*Evaluation Metrics*: To objectively assess and compare the performance of the different methods, we use three key evaluation metrics: Peak signal-to-noise ratio (PSNR), structural similarity index (SSIM), and spectral angle mapper (SAM). These metrics are widely used in image processing and remote sensing to evaluate the quality, fidelity, and spectral accuracy of images. PSNR measures the overall signal fidelity by comparing the peak error in pixel intensities. SSIM quantifies the perceptual similarity between two images, accounting for luminance, contrast, and structure. SAM, on the other hand, assesses the spectral similarity between the predicted HSI and the ground truth by calculating the angle between their respective spectral vectors. Together, these metrics provide a comprehensive evaluation of the model's performance in terms of both spatial and spectral

accuracy.

$$\text{MSE} = \frac{1}{N} \sum_{i=0}^N \|x_i - y_i\|^2 \quad (21)$$

$$\text{PSNR} = 10 \cdot \log_{10} \left( \frac{\text{MAX}_I^2}{\text{MSE}} \right) \quad (22)$$

where  $\text{MAX}_I$  is the maximum pixel value, for example, if each sample point is expressed in 8 bits,  $\text{MAX}_I$  is 255.  $x$  and  $y$  are the two images that are compared.  $N$  is the number of pixels  $x$  in and  $y$ .

$$\text{SSIM} = \frac{(2\mu_x\mu_y + c_1)(\sigma_{xy} + c_2)}{(\mu_x^2 + \mu_y^2 + c_1)(\sigma_x^2 + \sigma_y^2 + c_2)} \quad (23)$$

where  $\mu_x$  and  $\mu_y$  denote the means of  $x$  and  $y$ ,  $\sigma_x$  and  $\sigma_y$  represent the variances,  $\sigma_{xy}$  is the covariance, and  $c_1$ ,  $c_2$  are constant parameters

$$\text{SAM} = \frac{1}{N} \sum_{i=1}^N \arccos \left( \frac{x_i^\top y_i}{\|x_i\| \|y_i\|} \right) \quad (24)$$

where  $N$  is the number of pixels of  $x$  and  $y$ .

*Experimental Setup*: The experiments were conducted on an NVIDIA GeForce RTX 3090. The optimizer used for training was Adam, known for its efficient performance in deep learning tasks. The learning rate was set to 0.0005, and the model was trained for a total of 500 epochs. The determined loss weights are  $\alpha = 5$ ,  $\beta = 0.5$ , and  $\gamma = 1$ .

### C. Main Results

We compared our approach with five state-of-the-art methods: UnGun [55], HSRNet [70], HRNet [63], LTRN [71], MST++ [62], UNet [72], and ResNet50 [73]. MST++ won NTIRE 2022, and HRNet ranked first in the NTIRE 2020 “Real-World” track.

*Quantitative Results*: As shown in Table I, on the three widely used hyperspectral datasets, namely ICVL, DFC2018 Houston, and TG1HRSSC, our method demonstrates significant advantages over other competing methods. In the ICVL dataset, compared with the second-best method, our method improves the Peak PSNR by 1.14% and reduces the SAM by 5.18%. For the DFC2018 Houston dataset, compared with the second-best method, our method increases the PSNR by 0.90% and reduces the SAM by 0.99%. On the TG1HRSSC dataset, compared with the second-best method, our method improves the PSNR by 2.96% and reduces the SAM by 9.87%. These results indicate that our method significantly enhances the spatial and spectral reconstruction effects, providing not only better image fidelity, but also more accurate spectral information. The increase in PSNR implies better image quality, while the reduction in SAM shows that, compared with the sub-optimal method, our method can better maintain spectral accuracy and minimize spectral distortion. By effectively combining spectral priors with high-resolution spatial information, we ensure that both spatial and spectral features are enhanced, overcoming the limitations of existing methods in dealing with boundary artifacts and spectral distortion.

TABLE I  
FINAL TESTING RESULTS OF ICVL, DFC2018 HOUSTON, AND TG1HRS SC

| Dataset         |       | Ours           | UnGun          | HSRNet  | HRNet          | LTRN           | MST++   | UNet    |
|-----------------|-------|----------------|----------------|---------|----------------|----------------|---------|---------|
| ICVL            | PSNR↑ | <b>30.7029</b> | <u>30.3563</u> | 29.9221 | 29.8862        | 27.9452        | 28.0583 | 26.1978 |
|                 | SSIM↑ | <b>0.8851</b>  | <u>0.8834</u>  | 0.8378  | 0.8288         | 0.8413         | 0.7816  | 0.8475  |
|                 | SAM↓  | <b>5.8631</b>  | <u>6.1839</u>  | 6.5244  | 6.3900         | 7.5546         | 7.7055  | 7.7844  |
| DFC2018 Houston | PSNR↑ | <b>21.4816</b> | <u>21.2893</u> | 20.4453 | 21.1678        | 20.4955        | 20.8676 | 20.0862 |
|                 | SSIM↑ | <b>0.6273</b>  | <u>0.6140</u>  | 0.5953  | <u>0.6238</u>  | 0.5795         | 0.6052  | 0.5843  |
|                 | SAM↓  | <b>23.7292</b> | <u>24.6716</u> | 24.0021 | <u>23.9683</u> | 26.8290        | 25.1006 | 26.9005 |
| TG1HRS SC       | PSNR↑ | <b>23.9442</b> | <u>21.9273</u> | 22.6989 | 22.9399        | <u>23.2538</u> | 22.1450 | 20.3475 |
|                 | SSIM↑ | <b>0.6849</b>  | <u>0.6710</u>  | 0.6237  | <u>0.6791</u>  | 0.6537         | 0.6741  | 0.6263  |
|                 | SAM↓  | <b>10.1001</b> | <u>12.0977</u> | 11.7872 | <u>11.2071</u> | 11.3640        | 12.0784 | 14.2237 |

The best and second-best results are **bold** and underlined, respectively. ↑ the higher the better, and vice versa.

![Figure 6: Visualization results of seven methods on the ICVL dataset. The figure is a grid of images and error maps. The columns are labeled: GT, Ours, UnGun, HSRNet, HRNet, LTRN, MST++, and UNet. The rows are organized into four groups. The first group (rows 1 and 2) shows a bridge scene. The second group (rows 3 and 4) shows a dark scene with trees. The third group (rows 5 and 6) shows a street scene with a sign. The fourth group (rows 7 and 8) shows a tree scene. The first, third, and fifth rows show the generated images. The second, fourth, and sixth rows show the corresponding error maps. The error maps use a color scale from 0 (blue) to 0.5 (red). Red boxes highlight specific regions in the images and error maps for comparison.](7ff005f9556dc6518981bb92091d36ab_img.jpg)

Figure 6: Visualization results of seven methods on the ICVL dataset. The figure is a grid of images and error maps. The columns are labeled: GT, Ours, UnGun, HSRNet, HRNet, LTRN, MST++, and UNet. The rows are organized into four groups. The first group (rows 1 and 2) shows a bridge scene. The second group (rows 3 and 4) shows a dark scene with trees. The third group (rows 5 and 6) shows a street scene with a sign. The fourth group (rows 7 and 8) shows a tree scene. The first, third, and fifth rows show the generated images. The second, fourth, and sixth rows show the corresponding error maps. The error maps use a color scale from 0 (blue) to 0.5 (red). Red boxes highlight specific regions in the images and error maps for comparison.

Fig. 6. Visualization results of seven methods on the ICVL dataset are presented. The first, third, and fifth rows show the images generated from the HSIs. The second, fourth, and sixth rows present the error maps, which reflect the differences between the images generated by the network and the ground truth. In these error maps, the blue hues represent smaller errors, indicating higher accuracy.

*Qualitative Results:* To further assess the effectiveness of our method, we provide qualitative comparisons with six state-of-the-art methods. Figs. 6–8 show results on three different datasets, with each row containing a different comparison format. The first, third, and fifth rows show images generated

from the ground truth HSIs for direct visual comparison. These provide a clear understanding of how well the methods recover the fine spectral details of the original data. In the second, fourth, and sixth rows, we present spectral residual maps, which highlight the differences between the reconstructed and ground truth

![Figure 7: Visualization results of seven methods on the DFC2018 Houston dataset. The figure is a grid with 8 columns (GT, Ours, UnGun, HSRNet, HRNet, LTRN, MST++, UNet) and 6 rows. Rows 1, 3, and 5 show generated images with red boxes highlighting specific regions. Rows 2, 4, and 6 show corresponding error maps. A color bar on the right of each error map row indicates error magnitude from 0 (blue) to 1 (red). The 'Ours' column consistently shows lower error maps compared to other methods.](91be14371a97fb5ce9eeb29ae18d07c3_img.jpg)

Figure 7: Visualization results of seven methods on the DFC2018 Houston dataset. The figure is a grid with 8 columns (GT, Ours, UnGun, HSRNet, HRNet, LTRN, MST++, UNet) and 6 rows. Rows 1, 3, and 5 show generated images with red boxes highlighting specific regions. Rows 2, 4, and 6 show corresponding error maps. A color bar on the right of each error map row indicates error magnitude from 0 (blue) to 1 (red). The 'Ours' column consistently shows lower error maps compared to other methods.

Fig. 7. The visualization results of seven methods on the DFC2018 Houston dataset are presented. The first, third, and fifth rows show the images generated from the HSIs. The second, fourth, and sixth rows present the error maps, which reflect the differences between the images generated by the network and the ground truth. In these error maps, the blue hues represent smaller errors, indicating higher accuracy.

spectral values, further illustrating how well each method preserves spectral accuracy. In all three datasets, previous methods often fail to recover fine spectral details, especially along image boundaries, where they introduce artifacts and distortions. These methods also exhibit poor recovery of high-frequency spatial features, such as sharp edges, leading to blurry or inconsistent image reconstruction. In contrast, our approach preserves both the spectral and spatial continuity across the image. The images generated by our method show sharp, clear boundaries with no visible artifacts. The spectral residual maps further demonstrate that our method has lower residual errors in both spatial and spectral domains compared to the other methods. This consistency in both spectral and spatial fidelity illustrates the effectiveness of our method in generating high-quality HSIs, with improved global and local feature preservation.

### D. Ablation Analysis

To evaluate the contribution of each module in our network, we conducted a series of ablation experiments using the TG1HRSSC dataset. These experiments focused on three key

components: the spectral prior, the UMSR module, and the MSUT. The results from these ablation studies are summarized in Table II.

For model 1, we tested the impact of replacing the unmixing module in the UMSR with a ResNet-based architecture. This replacement caused a significant performance drop, with PSNR decreasing by 20.19%, SSIM by 32.95%, and SAM increasing by 59.44%. The large increase in SAM indicates a severe loss in spectral accuracy, and the significant drop in SSIM points to the failure of the ResNet-based architecture to preserve spatial features effectively. This clearly shows that the unmixing module is crucial for maintaining the spatial and spectral integrity of the image. The unmixing process helps in disentangling the spectral components of the image, which is essential for super-resolution tasks, particularly in hyperspectral imaging where both spatial and spectral fidelity are important.

For model 2, we replaced it with a traditional Swin Transformer using window sizes of 8, 4, and 2. This modification resulted in a considerable decrease in performance, with PSNR dropping by 13.94%, SSIM by 29.11%, and SAM increasing by 43.72%. The substantial decrease in PSNR and SSIM, coupled

![Figure 8: Visualization results of seven methods on the TG1HRSRC dataset. The figure is a grid of images and error maps. Columns represent: GT, Ours, UnGun, HSRNet, HRNet, LTRN, MST++, and UNet. Rows 1, 3, and 5 show reconstructed images with red boxes highlighting details. Rows 2, 4, and 6 show corresponding error maps. A color bar on the right of each row of error maps indicates error magnitude from 0 (blue) to 1 (red).](7801d00a216dc4dc8a7d210dcb5fe3c5_img.jpg)

Figure 8: Visualization results of seven methods on the TG1HRSRC dataset. The figure is a grid of images and error maps. Columns represent: GT, Ours, UnGun, HSRNet, HRNet, LTRN, MST++, and UNet. Rows 1, 3, and 5 show reconstructed images with red boxes highlighting details. Rows 2, 4, and 6 show corresponding error maps. A color bar on the right of each row of error maps indicates error magnitude from 0 (blue) to 1 (red).

Fig. 8. Visualization results of seven methods on the TG1HRSRC dataset are presented. The first, third, and fifth rows show the images generated from the HSIs. The second, fourth, and sixth rows present the error maps, which reflect the differences between the images generated by the network and the ground truth. In these error maps, the blue hues represent smaller errors, indicating higher accuracy.

TABLE II  
QUANTITATIVE RESULTS OF ABLATION EXPERIMENTS ON THE TG1HRSRC DATASET

| Model     | Unmixing | SWMS | point prior | PSU | PSNR $\uparrow$ | SSIM $\uparrow$ | SAM $\downarrow$ |
|-----------|----------|------|-------------|-----|-----------------|-----------------|------------------|
| 1         | ✗        | ✓    | ✓           | ✓   | 19.1079         | 0.4592          | 16.1042          |
| 2         | ✓        | ✗    | ✓           | ✓   | 20.6048         | 0.4853          | 14.5165          |
| 3         | ✓        | ✓    | ✗           | ✓   | 22.6758         | <u>0.6759</u>   | 11.2807          |
| 4         | ✓        | ✓    | ✓           | ✗   | <u>23.4625</u>  | 0.6722          | <u>10.6627</u>   |
| SPointNet | ✓        | ✓    | ✓           | ✓   | <b>23.9442</b>  | <b>0.6849</b>   | <b>10.1001</b>   |

The best and second-best results are **bold** and underlined, respectively.

with the increase in SAM, indicates that the traditional Swin Transformer struggled to effectively handle the spatial information. This highlights the superior performance of MSUT in preserving spatial information, particularly in tasks that require maintaining fine spatial structures and boundary details. The performance drop underscores the necessity of the MSUT, which allows for better spatial feature extraction and more accurate spatial information fusion.

For model 3, we replaced the spectral point input with a full-image input. This modification resulted in a noticeable decline in performance, with a PSNR decrease of 5.29%, a

reduction in SSIM by 1.31%, and an increase in SAM by 11.68%. These results suggest that using a full-image spectral prior introduces redundant information, which leads to spectral distortion and degrades the overall image quality. The larger SAM value indicates that the model was unable to preserve spectral details as effectively. This demonstrates the importance of using point-based spectral priors, which focus on the essential spectral features of the image, ensuring minimal redundancy, and better preservation of the spectral integrity.

For model 4, we examined the effect of removing the PSU operation within the MSUT. This change led to a decrease in

TABLE III  
PERFORMANCE OF OUR APPROACH WITH VARYING HYPER-PARAMETERS  $n$

| Dataset         | $n$              | 5       | 7              | 10             | 13             | 15      | 20      |
|-----------------|------------------|---------|----------------|----------------|----------------|---------|---------|
| ICVL            | PSNR $\uparrow$  | 30.6353 | 30.6418        | <b>30.7029</b> | <u>30.7019</u> | 30.6451 | 30.5931 |
|                 | SSIM $\uparrow$  | 0.8825  | 0.8834         | <b>0.8851</b>  | <u>0.8850</u>  | 0.8811  | 0.8791  |
|                 | SAM $\downarrow$ | 5.9190  | 5.9010         | <b>5.8631</b>  | <u>5.8654</u>  | 5.8741  | 5.9312  |
| DFC2018 Houston | PSNR $\uparrow$  | 20.4424 | 20.6440        | <b>21.4816</b> | <u>21.2243</u> | 20.6346 | 20.1775 |
|                 | SSIM $\uparrow$  | 0.6212  | 0.6204         | <b>0.6273</b>  | <u>0.6259</u>  | 0.6204  | 0.6222  |
|                 | SAM $\downarrow$ | 26.4487 | 25.7762        | <b>23.7292</b> | <u>24.2339</u> | 25.9309 | 27.2974 |
| TG1HRSRC        | PSNR $\uparrow$  | 22.0387 | <u>23.7902</u> | <b>23.9442</b> | 23.6509        | 23.5125 | 23.6521 |
|                 | SSIM $\uparrow$  | 0.6767  | <u>0.6810</u>  | <b>0.6849</b>  | 0.6804         | 0.6789  | 0.6795  |
|                 | SAM $\downarrow$ | 12.7628 | <u>10.1508</u> | <b>10.1001</b> | 10.2802        | 10.4622 | 10.5186 |

The best and second-best results are **bold** and underlined, respectively.

TABLE IV  
THE PERFORMANCE OF OUR APPROACH WITH VARYING HYPER-PARAMETERS  $\epsilon$

| $\epsilon$ | PSNR $\uparrow$ | SSIM $\uparrow$ | SAM $\downarrow$ |
|------------|-----------------|-----------------|------------------|
| 0.005      | 22.8677         | 0.6153          | 12.4387          |
| 0.010      | <b>23.9442</b>  | <b>0.6849</b>   | <b>10.1001</b>   |
| 0.050      | <u>22.9683</u>  | <u>0.6277</u>   | <u>11.6810</u>   |
| 0.100      | 20.5336         | 0.5923          | 13.8905          |

The best and second-best results are **bold** and underlined, respectively.

PSNR by 2.01%, a slight reduction in SSIM by 1.85%, and an increase in SAM by 5.57% . While the effect of removing PSU was less dramatic than other modifications, the results still suggest that PSU plays an important role in enhancing performance. The increase in SAM indicates a slight deterioration in spectral accuracy, and the reduction in SSIM implies that the spatial coherence of the image was also affected. The PSU operation aids in more effective rearrangement of image rows and columns, facilitating better global attention and improving the overall spatial and spectral reconstruction quality. This further supports the importance of PSU in our MSUT module and its contribution to improving the quality of hyperspectral super-resolution.

### E. Effect of Varying Point Number

We set the spectral sample points  $n$  and  $\epsilon$  to investigate its effect. As shown in Tables III and IV, the best results occur at  $n = 10$  and  $\epsilon = 0.010$ , so we use  $n = 10$  and  $\epsilon = 0.010$  in our experiments.

## V. CONCLUSION

In this article, we propose a novel SSR framework that introduces point-spectral priors into the PI-Fusion module, achieving more accurate spectral information injection while reducing input redundancy. The UMSR module enhances spectral fidelity, and the MSUT module further refines spatial details by fusing RGB images with coarse HSI, resulting in high-quality hyperspectral reconstruction with both spectral consistency and spatial clarity. Experimental results demonstrate that our method outperforms state-of-the-art approaches on three public datasets.

We also envision several promising directions for future work. First, enhancing the generalizability of the model across diverse environments and data sources will be crucial for broader applicability. Second, we plan to explore real-time deployment strategies to enable practical usage in field applications. Moreover, the proposed method holds great potential in various real-world scenarios, such as agricultural monitoring, medical imaging, and ecological assessments, where high-resolution spectral information is essential. We believe these extensions will further improve the practical value of our approach.

## REFERENCES

- [1] F. Melgani and L. Bruzzone, "Classification of hyperspectral remote sensing images with support vector machines," *IEEE Trans. Geosci. Remote Sens.*, vol. 42, no. 8, pp. 1778–1790, Aug. 2004.
- [2] J. M. Bioucas-Dias, A. Plaza, G. Camps-Valls, P. Scheunders, N. Nasrabadi, and J. Chanussot, "Hyperspectral remote sensing data analysis and future challenges," *IEEE Geosci. Remote Sens. Mag.*, vol. 1, no. 2, pp. 6–36, Jul. 2013.
- [3] A. Samat, E. Li, P. Du, S. Liu, and Z. Miao, "Improving deep forest via patch-based pooling, morphological profiling, and pseudo labeling for remote sensing image classification," *IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens.*, vol. 14, pp. 9334–9349, Sep. 2021.
- [4] A. Samat, E. Li, W. Wang, S. Liu, and X. Liu, "HOLP-DF: HOLP based screening ultrahigh dimensional subfeatures in deep forest for remote sensing image classification," *IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens.*, vol. 15, pp. 8287–8298, Sep. 2022.
- [5] Q. Liu, X. Meng, F. Shao, and S. Li, "Supervised-unsupervised combined deep convolutional neural networks for high-fidelity pansharpening," *Inf. Fusion*, vol. 89, pp. 1566–2535, Jan. 2023.
- [6] Q. Liu, K. Ren, X. Meng, and F. Shao, "Domain adaptive cross-reconstruction for change detection of heterogeneous remote sensing images via a feedback guidance mechanism," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, pp. 1–16, Oct. 2023.
- [7] Q. Liu, X. Chen, X. Meng, H. Chen, F. Shao, and W. Sun, "Dual-task interactive learning for unsupervised spatio-temporal-spectral fusion of remote sensing images," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, pp. 1–15, Apr. 2023.
- [8] B. Xi, J. Li, Y. Li, R. Song, D. Hong, and J. Chanussot, "Few-shot learning with class-covariance metric for hyperspectral image classification," *IEEE Trans. Image Process.*, vol. 31, pp. 5079–5092, Jul. 2022.
- [9] B. Liu, X. Yu, A. Yu, P. Zhang, G. Wan, and R. Wang, "Deep few-shot learning for hyperspectral image classification," *IEEE Trans. Geosci. Remote Sens.*, vol. 57, no. 4, pp. 2290–2304, Oct. 2018.
- [10] S. Mei, X. Chen, Y. Zhang, J. Li, and A. Plaza, "Accelerating convolutional neural network-based hyperspectral image classification by step activation quantization," *IEEE Trans. Geosci. Remote Sens.*, vol. 60, pp. 1–12, Feb. 2021.

- [11] S. Mei, J. Ji, Y. Geng, Z. Zhang, X. Li, and Q. Du, "Unsupervised spatial-spectral feature learning by 3D convolutional autoencoder for hyperspectral classification," *IEEE Trans. Geosci. Remote. Sens.*, vol. 57, no. 9, pp. 6808–6820, Apr. 2019.
- [12] H. Akbari, Y. Kosugi, K. Kojima, and N. Tanaka, "Detection and analysis of the intestinal ischemia using visible and invisible hyperspectral imaging," *IEEE Trans. Biomed. Eng.*, vol. 57, no. 8, pp. 2011–2017, May 2010.
- [13] Y. Shi, J. Li, Y. Zheng, B. Xi, and Y. Li, "Hyperspectral target detection with roi feature transformation and multiscale spectral attention," *IEEE Trans. Geosci. Remote. Sens.*, vol. 59, no. 6, pp. 5071–5084, Jul. 2020.
- [14] Z. Pan, G. Healey, M. Prasad, and B. Tromberg, "Face recognition in hyperspectral images," *IEEE Trans. Pattern. Anal. Mach. Intell.*, vol. 25, no. 12, pp. 1552–1560, Dec. 2003.
- [15] V. Backman et al., "Detection of preinvasive cancer cells," *Nature*, vol. 406, pp. 35–36, Jul. 2000.
- [16] T. Akgun, Y. Altunbasak, and R. M. Mersereau, "Super-resolution reconstruction with roi hyperspectral images," *IEEE Trans. Image Process.*, vol. 14, no. 11, pp. 1860–1875, Oct. 2005.
- [17] S. Gou, S. Liu, S. Yang, and L. Jiao, "Remote sensing image super-resolution reconstruction based on nonlocal pairwise dictionaries and double regularization," *IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens.*, vol. 7, no. 12, pp. 4784–4792, Jun. 2014.
- [18] H. Zhang, L. Zhang, and H. Shen, "A super-resolution reconstruction algorithm for hyperspectral images," *Signal Process.*, vol. 92, no. 9, pp. 2082–2096, Sep. 2012.
- [19] H. Irmak, G. B. Akar, and S. E. Yuksel, "A map-based approach for hyperspectral imagery super-resolution," *IEEE Trans. Image Process.*, vol. 27, no. 6, pp. 2942–2951, Mar. 2018.
- [20] Q. Wang, Q. Li, and X. Li, "Spatial-spectral residual network for hyperspectral image super-resolution," arXiv:2001.04609, Jan. 2020.
- [21] Q. Li, Q. Wang, and X. Li, "Exploring the relationship between 2D/3D convolution for hyperspectral image super-resolution," *IEEE Trans. Geosci. Remote. Sens.*, vol. 59, no. 10, pp. 8693–8703, Jan. 2021.
- [22] X. Hu et al., "Hdnet: High-resolution dual-domain learning for spectral compressive imaging," in *CVPR*, 2022, pp. 17542–17551.
- [23] T. Huang, W. Dong, X. Yuan, J. Wu, and G. Shi, "Deep gaussian scale mixture prior for spectral compressive imaging," in *CVPR*, 2021, pp. 16216–16225.
- [24] Z. Meng, J. Ma, and X. Yuan, "End-to-end low cost compressive spectral imaging with spatial-spectral self-attention," in *ECCV*, Nov. 2020, pp. 187–204.
- [25] X. Wang, J. Ma, and J. Jiang, "Hyperspectral image super-resolution via recurrent feedback embedding and spatial-spectral consistency regularization," *IEEE Trans. Geosci. Remote. Sens.*, vol. 60, pp. 1–13, 2022.
- [26] O. Sidorov and J. Yngve Hardeberg, "Deep Hyperspectral Prior: Single-Image Denoising, Inpainting, Super-Resolution," in *Proc. IEEE/CVF Int. Conf. Comput. Vis. Workshops*, Oct. 2019.
- [27] J. Jiang, H. Sun, X. Liu, and J. Ma, "Learning spatial-spectral prior for super-resolution of hyperspectral imagery," *IEEE Trans. Comput. Imag.*, vol. 6, pp. 1082–1096, May 2020.
- [28] R. Dian, S. Li, L. Fang, T. Lu, and J. M. Bioucas-Dias, "Nonlocal sparse tensor factorization for semiblind hyperspectral and multispectral image fusion," *IEEE Trans. Cybern.*, vol. 50, no. 10, pp. 4469–4480, Nov. 2019.
- [29] Z. Zhu, H. Liu, J. Hou, H. Zeng, and Q. Zhang, "Semantic-Embedded Unsupervised Spectral Reconstruction From Single RGB Images in the Wild," in *ICCV*, 2021, pp. 2279–2288.
- [30] J. Li, Y. Leng, R. Song, W. Liu, Y. Li, and Q. Du, "Mformer: Taming masked transformer for unsupervised spectral reconstruction," *IEEE Trans. Geosci. Remote. Sens.*, vol. 61, pp. 1–12, Apr. 2023.
- [31] A. Radford et al., "Learning transferable visual models from natural language supervision," in *Int. Conf. Mach. Learn.*, 2021, pp. 8748–8763.
- [32] M. Breuer and J. Albertz, "Geometric correction of airborne whiskbroom scanner imagery using hybrid auxiliary data," *Int. Arch. Photogrammetry Remote Sens.*, 2000.
- [33] D. Poli and T. Toutin, "Review of developments in geometric modelling for high resolution satellite pushbroom sensors," *Photogrammetric Rec.*, vol. 28, no. 137, pp. 58–73, Feb. 2012.
- [34] H. Du, X. Tong, X. Cao, and S. Lin, "A Prism-Based System for Multi-spectral Video Acquisition," in *ICCV*, Sep. 2009, pp. 175–182.
- [35] P. Llull et al., "Coded aperture compressive temporal imaging," *Opt. Exp.*, pp. 10526–10545, 2013.
- [36] A. Wagadarikar, R. John, R. Willett, and D. Brady, "Single disperser design for coded aperture snapshot spectral imaging," *Appl. Opt.*, pp. B44–B51, 2008.
- [37] A. A. Wagadarikar, N. P. Pitsianis, X. Sun, and D. J. Brady, "Video rate spectral imaging using a coded aperture snapshot spectral imager," *Opt. Exp.*, pp. 6368–6388, 2009.
- [38] Q. Guo, J. Zhang, C. Zhong, and Y. Zhang, "Change detection for hyperspectral images via convolutional sparse analysis and temporal spectral unmixing," *IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens.*, vol. 14, pp. 4417–4426, 2021.
- [39] C. Zou and X. Huang, "Hyperspectral image super-resolution combining with deep learning and spectral unmixing," *Signal Processing: Image Commun.*, vol. 84, 2020, Art. no. 115833.
- [40] L. Su, Y. Sui, and Y. Yuan, "An unmixing-based multi-attention gan for unsupervised hyperspectral and multispectral image fusion," *Remote Sens.*, vol. 15, no. 4, Feb. 2023.
- [41] D. Hong et al., "Endmember-guided unmixing network (EGU-Net): A general deep learning framework for self-supervised hyperspectral unmixing," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 33, no. 11, pp. 6518–6531, Nov. 2022.
- [42] M. Zhao, L. Yan, and J. Chen, "LSTM-DNN based autoencoder network for nonlinear hyperspectral image unmixing," *IEEE J. Sel. Topics Signal Process.*, vol. 15, no. 2, pp. 295–309, Jan. 2021.
- [43] A. Ali et al., "XCIT: Cross-covariance image transformers," *NeurIPS*, 2021.
- [44] A. Dosovitskiy et al., "An image is worth 16x16 words: Transformers for Image recognition at scale," *arXiv:2010.11929*, 2020.
- [45] C.-F. R. Chen, Q. Fan, and R. Panda, "Crossvit: Cross-attention multi-scale vision transformer for image classification," in *ICCV*, 2021.
- [46] Z. Dai, B. Cai, Y. Lin, and J. Chen, "UP-DETR: Unsupervised pre-training for object detection with transformers," in *CVPR*, 2021.
- [47] X. Dai, Y. Chen, J. Yang, P. Zhang, L. Yuan, and L. Zhang, "Dynamic Detr: End-to-end object detection with dynamic attention," in *ICCV*, 2021.
- [48] N. Carion, F. Massa, G. Synnaeve, N. Usunier, A. Kirillov, and S. Zagoruyko, "End-to-end object detection with transformers," in *ECCV*, Nov. 2020.
- [49] E. Xie, W. Wang, Z. Yu, A. Anandkumar, J. M. Alvarez, and P. Luo, "Segformer: Simple and Efficient Design for Semantic Segmentation With Transformers," *NeurIPS*, 2021.
- [50] N. Kim, D. Kim, C. Lan, W. Zeng, and S. Kwak, "ReSTR: Convolution-free referring image segmentation using transformers," in *CVPR*, 2022.
- [51] C. Lu, D. de Geus, and G. Dubbelman, "Content-aware token sharing for efficient semantic segmentation with vision transformers," in *CVPR*, 2023.
- [52] S. Zheng et al., "Rethinking semantic segmentation from a sequence-to-sequence perspective with transformers," in *CVPR*, 2021.
- [53] Y. Xu, Z. Wu, J. Chanussot, and Z. Wei, "Nonlocal patch tensor sparse representation for hyperspectral image super-resolution," *IEEE Trans. Image Process.*, Jan. 2019.
- [54] S. Li, R. Dian, L. Fang, and J. M. Bioucas-Dias, "Fusing hyperspectral and multispectral images via coupled sparse tensor factorization," *IEEE Trans. Image Process.*, May 2018.
- [55] Q. Qu, B. Pan, X. Xu, T. Li, and Z. Shi, "Unmixing guided unsupervised network for RGB spectral super-resolution," *IEEE Trans. Image Process.*, Aug. 2023.
- [56] Y. Cai et al., "Mask-guided spectral-wise transformer for efficient hyperspectral image reconstruction," in *CVPR*, 2022.
- [57] Y. Cai et al., "Coarse-to-fine sparse transformer for hyperspectral image reconstruction," in *ECCV*, Oct. 2022.
- [58] B. Arad and O. Ben-Shahar, "Sparse recovery of hyperspectral signal from natural RGB images," in *ECCV*, Sep. 2016.
- [59] L. Gao, D. Hong, J. Yao, B. Zhang, P. Gamba, and J. Chanussot, "Spectral superresolution of multispectral imagery with joint sparse and low-rank learning," *IEEE Trans. Geosci. Remote. Sens.*, Jun. 2020.
- [60] K. Zhang, T. Jin, F. Zhang, and J. Sun, "Long-short attention network for the spectral super-resolution of multispectral images," in *ICASSP*, May 2023.
- [61] Z. Shi, C. Chen, Z. Xiong, D. Liu, and F. Wu, "Hscnn : Advanced CNN-based hyperspectral recovery from RGB images," in *CVPRW*, 2018.
- [62] Y. Cai et al., "MST : Multi-stage spectral-wise transformer for efficient spectral reconstruction," in *CVPR*, 2022.
- [63] Y. Zhao, L.-M. Po, Q. Yan, W. Liu, and T. Lin, "Hierarchical regression network for spectral reconstruction from RGB images," in *CVPR*, 2020.
- [64] B. Chen, L. Liu, C. Liu, Z. Zou, and Z. Shi, "Spectral-cascaded diffusion model for remote sensing image spectral super-resolution," *IEEE Trans. Geosci. Remote Sens.*, vol. 62, pp. 1–14, Aug. 2024.
- [65] C. Zhou, Z. He, G. Lai, and A. Plaza, "A selective semantic transformer for spectral super-resolution of multispectral imagery," *IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens.*, vol. 18, pp. 7436–7450, Feb. 2025.

- [66] J. Li, K. Zheng, L. Gao, Z. Han, Z. Li, and J. Chanussot, "Enhanced deep image prior for unsupervised hyperspectral image super-resolution," *IEEE Trans. Geosci. Remote Sens.*, vol. 63, pp. 1–18, Jan. 2025.
- [67] X. Cao, Y. Lian, J. Li, K. Wang, and C. Ma, "Unsupervised multi-level spatio-spectral fusion transformer for hyperspectral image super-resolution," *Opt. Laser Technol.*, vol. 176, Sep. 2024, Art. no. 111032.
- [68] X. Cao, Y. Lian, K. Wang, C. Ma, and X. Xu, "Unsupervised hybrid network of transformer and CNN for blind hyperspectral and multispectral image fusion," *IEEE Trans. Geosci. Remote Sens.*, vol. 62, pp. 1–15, Jan. 2024.
- [69] S.-Q. Deng, L.-J. Deng, X. Wu, R. Ran, D. Hong, and G. Vivone, "PSRT: Pyramid shuffle-and-reshuffle transformer for multispectral and hyperspectral image fusion," *IEEE Trans. Geosci. Remote Sens.*, Feb. 2023.
- [70] J. He, J. Li, Q. Yuan, H. Shen, and L. Zhang, "Spectral response function-guided deep optimization-driven network for spectral super-resolution," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 33, no. 9, pp. 4213–4227, Feb. 2021.
- [71] R. Dian, Y. Liu, and S. Li, "Spectral super-resolution via deep low-rank tensor representation," *IEEE Trans. Neural Netw. Learn. Syst.*, pp. 1–11, Mar. 2024.
- [72] O. Ronneberger, P. Fischer, and T. Brox, "U-Net: Convolutional networks for biomedical image segmentation," in *MICCAI*, Nov. 2015.
- [73] K. He, X. Zhang, S. Ren, and J. Sun, "Deep residual learning for image recognition," in *CVPR*, 2016.

![Portrait of Xintao Zhong](0cc86fe8fc37b0edc9581f2af9459a52_img.jpg)

Portrait of Xintao Zhong

**Xintao Zhong** received the B.S. degree in electronic information science and technology from Zhuhai College of Jilin University, Zhuhai, China, in 2023. He is currently working toward the master's degree in communication engineering with Ningbo University, Ningbo, China.

His research interests are spectral super-resolution.

![Portrait of Shenfu Zhang](b8205e5e617a8946ddc956c816156fec_img.jpg)

Portrait of Shenfu Zhang

**Shenfu Zhang** received the B.S. degree in electronic information engineering from Shaoxing University, Shaoxing, China, in 2022. He is currently working toward the Ph.D. degree in information and communication engineering with Ningbo University, Ningbo, China.

His research interests include hyperspectral image processing and multisource data fusion classification.

![Portrait of Chenyang Lu](6b7b3f3d6f9341906163682cf12d1ea1_img.jpg)

Portrait of Chenyang Lu

**Chenyang Lu** received the B.Sc. degree in mechatronics engineering from Zhejiang University, Hangzhou, China, in 2017, and the M.Sc. degree in control systems technology from Eindhoven University of Technology (TU/e), the Netherlands, in 2018, and the Ph.D. degree in electrical and electronic engineering from TU/e, in 2023.

He is currently a Lecturer with the Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo, China. His research interests include computer vision, autonomous driving, and artificial intelligence.

![Portrait of Xuejian Sun](08e28a86c71221f509c8f3a828e89af2_img.jpg)

Portrait of Xuejian Sun

**Xuejian Sun** received the B.E. degree in surveying and mapping engineering from Tongji University, Shanghai, China, in 2010, and the Ph.D. degree in cartography and geographical information systems with the Institute of Remote Sensing and Digital Earth, Chinese Academy of Sciences, Beijing, China.

He is currently an Associate Researcher with the Aerospace Information Research Institute, Chinese Academy of Sciences, and a standing Director of the Chinese Remote Sensing Committee. He has long been engaged in applied research on hyperspectral remote sensing technology. He has developed a series of innovative software and hardware equipment with independent intellectual property rights in the fields of natural resources, ecological environment, cultural relics protection, and physical evidence identification, has published more than 30 high-level papers, and has applied for more than 20 patents.

![Portrait of Feng Shao](b6eb6de2eec0bcedfced4208ba3862f2_img.jpg)

Portrait of Feng Shao

**Feng Shao** (Senior Member, IEEE) received the B.S. and Ph.D. degrees from Zhejiang University, Hangzhou, China, in 2002 and 2007, respectively, all in electronic science and technology.

He is currently a Professor with the Faculty of Information Science and Engineering, Ningbo University, China. He was a Visiting Fellow with the School of Computer Engineering, Nanyang Technological University, Singapore, from February 2012 to August 2012. He has authored or coauthored more than 100 technical articles in refereed journals and proceedings in the areas of 3D video coding, 3D quality assessment, and image perception, etc.

Prof. Shao received "Excellent Young Scholar" Award by NSF of China (NSFC) in 2016.

![Portrait of Weiwei Sun](b06d67501749f81a31952444ff14fe18_img.jpg)

Portrait of Weiwei Sun

**Weiwei Sun** (Senior Member, IEEE) received the B.S. degree in surveying and mapping from Tongji University, Shanghai, China, in 2007, and the Ph.D. degree in cartography and geographic information engineering from Tongji University, in 2013.

From 2011 to 2012, he studied in the Department of Applied Mathematics, University of Maryland College Park, working as a visiting scholar with the famous Professor John Benedetto to study on the dimensionality reduction of Hyperspectral Image.

From 2014 to 2016, he studied in the State Key Laboratory for Information Engineering in Surveying, Mapping and Remote Sensing (LIESMARS), Wuhan University, working as a Postdoc to study intelligent processing in Hyperspectral imagery. From 2017 to 2018, He worked with the Department of Electrical and Computer Engineering, Mississippi State University, also working as a visiting scholar in hyperspectral image processing. He is currently a Full Professor with Ningbo University, Zhejiang Province, China, and. He has authored or coauthored more than 80 journal papers and his current research interests include hyperspectral image processing with machine learning.

![Portrait of Xiangchao Meng](1a4655ab13ebfd068a33364361d525ff_img.jpg)

Portrait of Xiangchao Meng

**Xiangchao Meng** (Senior Member, IEEE) received the B.S. degree in geographic information system from Shandong University of Science and Technology, Qingdao, China, in 2012, and the Ph.D. degree in cartography and geography information system from Wuhan University, Wuhan, China, in 2017.

He is currently a Professor with the Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo, China. He studied in the College of Electrical and Information Engineering, Hunan University, working as a Postdoc. His research interests include multisource data fusion, machine learning.