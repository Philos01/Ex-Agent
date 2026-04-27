

<!-- Page 1 -->

## Bidirectional Spectral Attention Multiscale Aggregation Network for Spectral Super-Resolution

Xintao Zhon[g](https://orcid.org/0009-0007-6795-4932) , Shenfu Zhang, Liang Chen, Gang Yang [,](https://orcid.org/0000-0002-7001-2037) Weiwei Su[n](https://orcid.org/0000-0003-3399-7858) , *Senior Member, IEEE*, Feng Shao [,](https://orcid.org/0000-0002-2495-9924) *Senior Member, IEEE*, and Xiangchao Meng [,](https://orcid.org/0000-0002-7405-3143) *Senior Member, IEEE*

*Abstract*— Spectral super-resolution (SSR) is the computational process of generating a high-dimensional hyperspectral image (HSI) from a low-dimensional image through spectral reconstruction techniques. Recently, deep learning has demonstrated remarkable potential in the field of SSR, achieving impressive results. However, existing deep learning-based approaches often fail to deliver high-fidelity SSR outcomes. These methods tend to focus primarily on spectral information while paying insufficient attention to the critical role of spatial features. Furthermore, they lack effective strategies for capturing interband relationships, resulting in suboptimal spectral information modeling. To address these limitations, we propose a novel network for SSR, termed bidirectional spectral attention multiscale aggregation network (BiSANet). BiSANet features three U-Netlike branches and integrates two advanced attention mechanisms. The bidirectional spectral attention modules dynamically model interspectral dependencies through forward and reverse spectral feature extraction, enhanced by a weight-sharing strategy. Specifically, we reverse the spectral order of feature maps to activate complementary global trends and local details, overcoming the limitations of unidirectional modeling in traditional methods. Additionally, an independent spatial reconstruction branch with a dedicated loss function ensures precise spatial detail preservation. Experimental results demonstrate that BiSANet outperforms state-of-the-art methods across three benchmarks. For instance, on the DFC2018 Houston dataset, it achieves a 4.26% peak signalto-noise ratio (PSNR) improvement and an 11.52% spectral angle mapper (SAM) reduction, highlighting its robustness and accuracy in spectral–spatial reconstruction.

*Index Terms*— Attention mechanism, deep learning, hyperspectral image (HSI), spectral super-resolution (SSR).

## I. INTRODUCTION

H YPERSPECTRAL image (HSI) enables per-pixel spectral characterization through contiguous narrow bands, driving its adoption in remote sensing [1], [2], [3], [4], [5], [6], food safe [7], [8], environmental monitoring [9],

Received 2 May 2025; revised 26 May 2025; accepted 27 May 2025. Date of publication 30 May 2025; date of current version 12 June 2025. This work was supported in part by Zhejiang Provincial Natural Science Foundation of China under Grant LR23D010001, in part by Project National Key Research and Development Program of China under Grant 2024YFF1400900, in part by the National Natural Science Foundation of China under Grant 42171326, and in part by Ningbo Natural Science Foundation under Grant 2022J076. *(Corresponding author: Xiangchao Meng.)*

Xintao Zhong, Shenfu Zhang, Liang Chen, Feng Shao, and Xiangchao Meng are with the Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo 315211, China (e-mail: 2311100200.nbu.edu.cn; zhangshenfu\_nbu@163.com; chenliang4@nbu.edu.cn; shaofeng@nbu.edu.cn; mengxiangchao@nbu.edu.cn).

Gang Yang and Weiwei Sun are with the Department of Geography and Spatial Information Techniques, Ningbo University, Ningbo 315211, China (e-mail: yanggang@nbu.edu.cn; sunweiwei@nbu.edu.cn).

Digital Object Identifier 10.1109/TGRS.2025.3575068

[10], [11], and geological exploration [12], [13]. However, due to the limitations of imaging technology, capturing HSI is time-consuming and complex, inevitably restricting the widespread application of HSI in practice.

When seeking to bypass the mechanical scanning constraints of conventional hyperspectral systems, researchers have proposed snapshot devices utilizing compressed sensing principles. These innovations, such as computed tomography imaging spectrometers (CTISs) [14], hybrid RGB-HS systems [15], and aperture masks [16], leverage computational reconstruction to achieve single-shot spectral data acquisition. The practicality of these systems remains constrained by their heavy dependence on costly hardware components. As a countermeasure, reconstruction of high-resolution HSI from RGB images has been proposed via spectral super-resolution (SSR) methodologies. By leveraging advanced algorithms, SSR reduces the cost of data acquisition and broadens the practical applications of hyperspectral technology, offering a promising alternative to hardware-intensive solutions.

Traditional SSR methods are primarily based on techniques such as spectral basis functions [17] and sparse dictionary [18]. However, these methods are limited by their restricted representational capacity and insufficient generalization performance. As a result, deep learning-based SSR approaches [19], [20], [21], [22], [23], [24], [25], [26], [27], [28], [29], [30], [31], [32] have gradually gained popularity and achieved impressive results. However, existing frameworks often struggle to balance spectral reconstruction and spatial detail preservation while lacking effective mechanisms for modeling bidirectional spectral–spatial interactions. These limitations lead to suboptimal performance in scenarios requiring high-fidelity reconstruction of both spectral correlations and fine-grained spatial structures.

To comprehensively extract spectral and spatial information and effectively model their complex interactions, this article proposes a novel framework called bidirectional spectral attention multiscale aggregation network (BiSANet). Two primary components constitute the framework: the spectral–spatial fusion and interaction module (SSFIM) and the reconstruction module. SSFIM is composed of the multispectral attention block (MSEB), reverse MSEB (RMSEB), and multispatial attention block (MSAB). All three blocks adopt a U-shaped structure to extract the multiresolution spectral and spatial contextual information critical for HSI reconstruction. Noticeably, MSEB and RMSEB have the same network structure.

<!-- Page 2 -->

Fig. 1. Diagram of bidirectional spectral attention modeling.

In SSFIM, MSEB and RMSEB jointly extract spectral information. MSEB integrates the spectral extraction block (SEB)—driven by spectral-wise multihead self-attention (S-MSA) [24]—to systematically harvest spectral correlations within the spectral axis. Although bidirectional attention mechanisms have been explored in fields such as video super-resolution [33], [34], their application in SSR remains unprecedented. This study pioneers the introduction of bidirectional spectral attention modeling into the SSR task, achieving dynamic bidirectional capture of interspectral dependencies through forward and reverse spectral feature extraction (MSEB and RMSEB modules) combined with a weight-sharing strategy, as shown in Fig. 1. Specifically, a spectral-dimension reversal is performed on the RMSEB module's feature maps to enhance interspectral relationship capture and activate bidirectional attention mechanisms. This design breaks through the limitation of traditional SSR methods, which model spectral features unidirectionally, providing a more comprehensive perspective for cross-band information interaction. By sharing weights, MSEB and RMSEB achieve bidirectional spectral information complementarity, significantly improving the effectiveness of spectral feature extraction.

The SAB module, comprising window-based multihead self-attention (W-MSA) and its shifted variant (SW-MSA) [35], forms the fundamental architecture of MSAB. To fully utilize the hierarchical relationships between features, an independent RGB image reconstruction branch is designed to inject multistage spatial information into MSEB and RMSEB dynamically. This enhances the spectral branch's ability to perceive spatial features. Additionally, to ensure the accuracy of spatial information extraction, an independent reconstruction loss is applied to optimize MSAB.

In recent years, vision state-space models (VSSMs), typified by Mamba, have emerged as a promising alternative to Transformers for image tasks. Mamba's state-space formulation enables linear computational complexity and efficient long-range dependency modeling, making it well-suited for processing high-dimensional HSIs that demand precise capture of spatial–spectral correlations. For instance, Xiao et al. [36] proposed frequency-assisted Mamba (FMSR) for remote sensing SR, demonstrating that integrating Mamba's global modeling with frequency-domain analysis balances global context and local details under linear complexity, addressing traditional methods' limitations.

This progress motivates our integration of Vision Mamba into the reconstruction module, where spectral information from bidirectional MSEB and RMSEB is adaptively fused using its powerful global attention modeling [37] and CBAM's spectral–spatial self-attention [38]. This combination ensures adaptive fusion that strengthens spectral–spatial consistency, crucial for high-fidelity HSI reconstruction.

The principal contribution of this work includes.

- 1) We proposed BiSANet, a novel SSR network designed to efficiently extract and integrate spatial and spectral features to enhance SSR accuracy.
- 2) We introduce three key self-designed modules to achieve this goal: a) the bidirectional spectral attention blocks (MSEB and RMSEB), which leverage weight-sharing to capture forward and reverse spectral dependencies, addressing the unidirectional modeling limitation of prior methods; b) an independent spatial feature extraction branch (MSAB) with a dedicated RGB reconstruction loss, ensuring precise spatial detail extraction and its multistage fusion with spectral features; and c) an adaptive reconstruction module that fuses Vision Mamba's global modeling and CBAM's spectral–spatial attention to dynamically integrate bidirectional spectral information.
- 3) Extensive experiments on three benchmark datasets demonstrate that BiSANet achieves state-of-the-art performance, outperforming existing methods in reconstruction fidelity and spectral consistency, validating the effectiveness of the proposed framework.

## II. RELATED WORKS

## *A. HSI Acquisition*

Traditional hyperspectral imaging systems typically use spectrometers to scan the target step by step in the spatial or spectral dimensions. Common methods include whiskbroom, pushbroom, and band sequential scanners. These techniques are widely used in fields such as remote sensing, environmental monitoring, and medical imaging. For example, whiskbroom and pushbroom methods have been applied to photogrammetry and remote sensing tasks in satellite sensors [39], [40]. However, these methods are time-consuming and cannot meet the demands of dynamic scenes. Additionally, these imaging systems are large in size and not suitable for portable applications. To address these challenges, snapshot compressed imaging (SCI) systems [41], [42], [43] and computational reconstruction algorithms [44], [45], [46], [47], [48], [49] have been developed. Among SCI systems, coded aperture snapshot spectral imaging (CASSI) [50] has gained attention due to its compact design and high efficiency. However, even relatively low-cost SCI systems typically range from tens of thousands to over a hundred thousand dollars, which limits their adoption in the consumer market. This further emphasizes the importance and practical significance of HSI super-resolution research.

## *B. Deep-Learning-Base SSR*

Currently, CNN-based models are increasingly being developed to capture nonlinear correlations between RGB and HSI

<!-- Page 3 -->

data through deep feature abstraction. Xiong et al. [51] introduced an innovative deep-learning architecture that processes spectral undersampling data through configurable network modules, systematically examining multiple structural variants for hyperspectral reconstruction. This CASSI-enhanced methodology pioneers a new pathway distinct from conventional compressed sensing paradigms. Shi et al. [52] designed HSCNN+ based on their previously proposed HSCNN model and achieved first place in the NTIRE 2018 Spectral Reconstruction Challenge [53]. Stiebel et al. [54] developed a modified U-Net architecture incorporating multiscale feature fusion modules for semantic segmentation tasks, achieving fourth position in the NTIRE 2018 spectral reconstruction challenge. Their enhanced framework demonstrated superior performance through optimized decoder pathways and refined skip connections compared to conventional U-Net implementations. The emergence of the self-attention mechanism [55] and its significant success in the field of computer vision have led most researchers to realize that selectively allocating network resources to the more important regions of feature maps can greatly enhance network performance. Currently, most self-attention works [38], [56], [57], [58] primarily achieve spatial or channel attention mechanisms by compressing spatial or channel dimensions through pooling layers. Peng et al. [59] proposed a pixel attention (PA) module to adaptively rescale pixel-level features across all feature maps. Li et al. [23] designed an adaptive channel weighting mechanism that models interchannel dependencies and optimizes feature distribution, securing first place in the "Clean" track and third position in the "Real World" track at the NTIRE 2020 Spectral Reconstruction Challenge. Following the outstanding performance of Vision Transformer [60] in the field of computer vision, researchers began to adopt multihead attention mechanisms to achieve higher quality hyperspectral reconstruction results [24], [45], [61]. Cai et al. [24] proposed spectral intelligent multihead self-attention based on the spatial sparsity and spectral self-similarity properties of HSI, achieving the first place in the NTIRE 2022 Spectral Reconstruction Challenge.

Despite the progress, existing deep learning-based SSR methods still face critical limitations in effectively modeling spectral–spatial interactions and multiscale feature integration. These can be broadly categorized into two key challenges.

*1) Insufficient Exploration of Spectral and Spatial Information:* Many existing methods prioritize spectral reconstruction while neglecting the extraction of fine-grained spatial details. This imbalance often results in blurred or distorted spatial dimensions, compromising the quality of reconstructed HSIs. Among these approaches, MST++ [24] employs spectralwise self-attention along with a U-shaped structure to retain partial spatial information, MFormer [26] uses an unsupervised framework that implicitly constrains spatial details via spectral structural similarity loss while its dual spectral attention and mask-guided band augmentation modules focus predominantly on spectral features, and SSRNet [19] connects spatial and spectral subnetworks through cross-fusion and incorporates an imaging model guidance module for spectral optimization; however, all of these methods lack dedicated spatial attention mechanisms, which can lead to slight spatial blurring, minor edge distortions during multiscale processing. Recent advances in multiscale feature fusion for computer vision tasks, such as MSPFN [62] and MSHFN [63], have demonstrated that hierarchical pyramid structures can effectively capture complementary information across scales. However, these spatial-domain multiscale approaches do not address the unique challenge in SSR, where the bidirectional correlations between spectral bands and the cross-modal interaction between spectral and spatial features require a more sophisticated fusion strategy. Overall, while each method makes valuable contributions to spectral reconstruction, there is an opportunity to further balance the integration of spectral and spatial information via multiscale, multilevel feature interaction, thereby enhancing the clarity and structural fidelity of the reconstructed images.

*2) Inadequate Interaction Between Spectral and Spatial Information:* Existing methods demonstrate strong individual feature extraction capabilities. For example, MSFN [20] processes features sequentially through independent spectral and spatial modules, with post hoc fusion modules integrating these streams; HSACS [21] employs a hybrid 2-D–3-D architecture that couples 2-D spatial features with 3-D spectral processing via channel expansion, with its second-order attention modules operating within each dimension; additionally, the camera spectral sensitivity prior is incorporated through loss functions. Overall, while each method exhibits its own strengths, there remains an opportunity to further enhance the interaction between spectral and spatial information through an end-to-end joint modeling framework that supports real-time bidirectional interaction and dynamic co-optimization, which could lead to improved reconstruction quality.

## III. METHODOLOGY

## *A. Problem Definition*

Let X ∈ R *H*×*W*×3 represent an RGB image and Y ∈ R *H*×*W*×*C* represent an HSI, where *W* and *H* represent the spatial width and height of the images, respectively, and *C* indicates the spectral channel count in the HSI. SSR seeks to establish a parametric mapping *f* (X; θ ) that recovers Y from X, with standard implementation involving optimization of the following objective function:

$$\arg\min_{\theta} \mathcal{L}_1(f(\mathbf{X};\theta), \mathbf{Y}) \tag{1}$$

where L<sup>1</sup> is a loss function.

The spectral response *Ic*(*x*, *y*) of an RGB imaging device at coordinate (*x*, *y*) can be mathematically modeled in spectral imaging as follows:

$$I_c(x, y) = \int F(x, y, \lambda) S_c(\lambda) d\lambda$$
 (2)

where *c* ∈ {*R*, *G*, *B*} indicates the color channel, *F*(*x*, *y*, λ) represents the spectral radiance at position (*x*, *y*) and wavelength λ, and *Sc*(λ) denotes the spectral response function for channel *c*.

<!-- Page 4 -->

In practical scenarios, since the wavelength range is typically sampled discretely, (2) can be reformulated as follows:

$$I_c(x, y) = \sum_{n=0}^{\infty} F(x, y, \lambda_i) S_c(\lambda_i)$$
 (3)

where n refers to the number of discrete spectral bands.

## B. Our Architecture

The network structure is illustrated in Fig. 2(a), where an RGB image  $\mathbf{X} \in \mathbb{R}^{H \times W \times 3}$  serves as the input, and it undergoes shallow feature extraction, fusion, and interaction of spectral and spatial information, and finally passes through the reconstruction module to output the HSI  $\hat{\mathbf{Y}} \in \mathbb{R}^{H \times W \times C}$ . In SSFIM, to ensure the accuracy of the extracted spatial information, unlike previous works that integrate spatial information extraction as part of the entire network, we independently design an RGB image reconstruction branch, namely MSAB, to extract spatial information. Additionally, an independent loss function is used to constrain the reconstructed RGB image  $\hat{\mathbf{X}} \in \mathbb{R}^{H \times W \times 3}$ , ensuring that the extracted spatial information remains accurate. The following equations can express this process:

$$\mathbf{F}_s = \text{GELU}(\text{Conv}_{1\times 1}(\mathbf{X})) \tag{4}$$

$$\mathbf{F}_{\text{Vim}} = \text{VisionMamba}(\mathbf{F}_s)$$
 (5)

$$[\mathbf{F}_{\text{SSFIM}}, \hat{\mathbf{X}}] = \text{SSFIM}(\mathbf{F}_{\text{Vim}})$$
 (6)

$$\mathbf{Y} = \mathbf{F}_s + \text{Rec}(\mathbf{F}_{\text{SSFIM}}) \tag{7}$$

where GELU refers to the GELU activation function,  $Conv_{1\times 1}$  represents the convolution operation with a  $1\times 1$  kernel, Vim refers to Vision Mamba [37], Rec denotes the reconstruction module, and  $\mathbf{F}_s \in \mathbb{R}^{H\times W\times C}$  and  $\mathbf{F}_{SSFIM} \in \mathbb{R}^{H\times W\times C}$  are intermediate features.

The spatial-spectral feature extraction and integration procedures of SSFIM are shown in Fig. 2(b). The module consists of three main branches: MSEB, RMSEB, and MSAB, which are responsible for the extraction and fusion of spectral and spatial information. Specifically, MSEB and RMSEB are used for spectral feature extraction. Building upon bidirectional propagation mechanisms in video super-resolution, RMSEB adopts reverse-order spectral feature extraction to enhance information capture across spectral bands. MSEB and RMSEB share weights, ensuring that the sequential and reverse spectral features complement each other. The physical intuition of bidirectional spectral dimension modeling arises from the continuity and symmetry of spectral data. For instance, the reflectance of the same object across adjacent bands typically exhibits smooth transitions, which manifest as complementary gradual patterns in forward  $(\lambda_1 \rightarrow \lambda_2)$  and reverse  $(\lambda_2 \rightarrow \lambda_1)$ processing. By capturing these forward and reverse spectral gradients through MSEB and RMSEB, the model comprehensively perceives both global trends (e.g., overall reflectance changes) and local details (e.g., interband gradual variations). Theoretically, this design aligns with symmetry analysis in signal processing, leveraging bidirectional feature extraction to capture spectral dependencies, while adhering to transfer learning principles through weight sharing to learn common spectral patterns and explore unique reverse-processing characteristics (e.g., edge effects). This approach improves efficiency and avoids overfitting, overcoming the limitations of traditional unidirectional modeling [24].

MSAB is a specially designed RGB image reconstruction branch aimed at extracting precise spatial information. All branches adopt a U-Net-like structure, with multiple downsampling and upsampling operations to achieve multiscale feature extraction, capturing both spatial and spectral information more comprehensively. Moreover, the spatial information extracted at each level by MSAB is equally fused into each level of MSEB and RMSEB, enabling deep fusion of spectral and spatial information. The physical intuition behind the independent spatial branch lies in the physical independence of spatial structures and spectral features in HSI. For example, an object's spatial contours are decoupled from its reflectance in specific bands, such as building edges and high reflectance in blue bands. Traditional methods coupling spatial information with spectral processing risk blurring spatial details during spectral processing. BiSANet's independent MSAB branch ensures spatial feature integrity through dedicated spatial attention, theoretically supported by multitask learning, defining spatial feature extraction as an independent sub-task for collaborative optimization with spectral reconstruction and hierarchical feature fusion. By integrating spatial features from MSAB into different levels of MSEB/RMSEB via multistage fusion, this design adheres to the feature pyramid network (FPN) principle, effectively capturing long-range cross-modal dependencies unattainable by traditional post-hoc fusion methods [20].

To simplify this article and avoid redundancy, we focus solely on the information exchange between MSAB and MSEB, as their interaction mirrors that of MSAB and RMSEB. The architectural configuration shown in Fig. 2(b) reveals that MSEB and MSAB employ symmetrical U-shaped topology. This framework incorporates three principal components: a downsampling encoder module for hierarchical feature extraction, a dimensionality-reduced intermediary layer serving as a latent representation, and an upsampling decoder component for spatial resolution restoration. To optimize information flow across network depths, cross-level bridging pathways are established between corresponding encoder—decoder stages, effectively addressing vanishing gradients while ensuring the stability of the training process.

Let the spectral and spatial branch features at level l, denoted as  $\mathbf{F}_{\text{SEB}_l}$  and  $\mathbf{F}_{\text{SAB}_l}$ , respectively, be in  $\mathbb{R}^{(H/2^{l-1})\times (W/2^{l-1})\times B}$  for l=1,2,3 or in  $\mathbb{R}^{(H\times 2^{l-3})\times (W\times 2^{l-3})\times B}$  for l=4,5,B represents the spectral dimension of the hidden layer.

In the first and second spectral–spatial encoding stages of the network, the spectral feature  $\mathbf{F}_{SEB_1}$  and the spatial feature  $\mathbf{F}_{SAB_1}$  from the previous stage are downsampled, fused, and then processed by the SEB to enhance the interaction and propagation of spectral and spatial information. The following equations can express this process:

$$\mathbf{F}_{\text{SEB}_{\perp}} = \text{SEB}(\mathbf{F}_{\text{Vim}}) \tag{8}$$

<!-- Page 5 -->

Fig. 2. Overall framework of BiSANet. (a) BiSANet. (b) Spectral-spatial fusion and interaction block. (c) FFN. (d) Spatial attention block. (e) Spectral attention block. (f) Reconstruction block.

$$\mathbf{F}_{\mathsf{SAB}_{\mathsf{L}}} = \mathsf{SAB}(\mathbf{X}) \tag{9}$$

$$\mathbf{F}_{\text{SEB}_2} = \text{SEB} \left( D(\mathbf{F}_{\text{SEB}_1}) + D(\mathbf{F}_{\text{SAB}_1}) \right) \tag{10}$$

$$\mathbf{F}_{SAB_2} = SAB(D(\mathbf{F}_{SAB_1})) \tag{11}$$

$$\mathbf{F}_{SEB_3} = SEB(D(\mathbf{F}_{SEB_2}) + D(\mathbf{F}_{SAB_2}))$$
 (12)

where D represents the downsampling operation.

In the third and fourth encoding stages, the same fusion process is repeated using the outputs  $\mathbf{F}_{SEB_3}$  and  $\mathbf{F}_{SAB_3}$  from the previous stage, enabling the model to capture richer low-resolution features layer by layer. The following equations can express this process:

$$\mathbf{F}_{SAB_3} = SAB(D(\mathbf{F}_{SAB_2})) \tag{13}$$

$$\mathbf{F}_{s_1} = U(\mathbf{F}_{SEB_3}) + U(\mathbf{F}_{SAB_3}) \tag{14}$$

where U represents the upsampling operation,  $\mathbf{F}_{s_1}$  represents the intermediate feature maps obtained during the information interaction process.

In the fourth spectral encoding stage, a  $1 \times 1$  convolution concatenates  $\mathbf{F}_{s_1} \in \mathbb{R}^{(H/4) \times (W/4) \times B}$  with the second-level spectral feature  $\mathbf{F}_{\text{SEB}_2}$  for convolutional fusion, followed by processing with the SEB to reinforce interlevel feature interactions. The following equation can express this process:

$$\mathbf{F}_{SEB_4} = SEB(Conv_{1\times 1}(Cat(\mathbf{F}_{s_1}, \mathbf{F}_{SEB_2})))$$
 (15)

where Cat represents the concatenation operation performed along the spectral dimension.

The fourth-level spectral and spatial features are upsampled and summed to obtain the fused feature  $\mathbf{F}_{s_2}$ , completing the pyramid-style feature fusion and enabling deep interaction of spectral and spatial information across scales. We concatenate  $\mathbf{F}_{\text{SEB}_5}$  with the  $\mathbf{F}_{\text{RSEB}_5}$  to generate the output of SSFIM, denoted as  $\mathbf{F}_{\text{SSFIM}}$ . Simultaneously, the reconstructed RGB image  $\hat{\mathbf{X}}$  is obtained through the MSAB. The following equations can express this process:

$$\mathbf{F}_{SAB_4} = SAB(U(\mathbf{F}_{SAB_3})) \tag{16}$$

$$\mathbf{F}_{s_2} = U(\mathbf{F}_{SEB_4}) + U(\mathbf{F}_{SAB_4}) \tag{17}$$

$$\mathbf{F}_{SEB_s} = SEB(Conv_{1\times 1}(Cat(\mathbf{F}_s, \mathbf{F}_{SEB_1})))$$
 (18)

$$\mathbf{F}_{\text{SSFIM}} = \text{Cat}(\mathbf{F}_{\text{SEB}_5}, \mathbf{F}_{\text{RSEB}_5}) \tag{19}$$

$$\hat{\mathbf{X}} = SAB(U(\mathbf{F}_{SAB_4})) \tag{20}$$

where  $\mathbf{F}_{s_2} \in \mathbb{R}^{(H/2) \times (W/2) \times B}$  represents the intermediate feature maps obtained during the information interaction process.

As shown in Fig. 2(f), we designed a novel reconstruction module. By leveraging the powerful global modeling capabilities of Vision Mamba [37] and the CBAM attention mechanism [38], the proposed module effectively utilizes the feature information extracted by SSFIM to accurately reconstruct the target HSI. The following equation can express

<!-- Page 6 -->

Fig. 3. Paradigms of different self-attention mechanisms. (a) Spectral-dimension attention mechanism: treating spectral bands as computation units for cross-channel dependency modeling. (b) Window-constrained spatial attention: establishing localized self-attention neighborhoods through fixed-grid spatial partitioning.

this process:

$$\hat{\mathbf{Y}} = \text{Rec}(\mathbf{F}_{\text{SSFIM}}) \tag{21}$$

where Rec represents the reconstruction block, and  $\hat{\mathbf{Y}} \in \mathbb{R}^{H \times W \times C}$  represents the finally output HSI.

## C. SEB and SAB

As illustrated in Fig. 2(d) and (e), to efficiently establish the correlation and connection between spectral and spatial information, we incorporated S-MSA [24] into the MSEB module. Additionally, W-MSA and SW-MSA [35] were introduced into the MSAB module.

As shown in Fig. 3(a), the SEB transforms input features through spectral tokenization. Given input feature map  $\mathbf{F} \in \mathbb{R}^{H \times W \times C}$  with spatial resolution  $H \times W$  and C spectral channels, the module first reshapes it into token sequence  $\mathbf{T} \in \mathbb{R}^{HW \times C}$ , where each row vector encapsulates spectral characteristics of a spatial position. Three trainable parameter matrices  $\mathbf{W}_Q, \mathbf{W}_K, \mathbf{W}_V \in \mathbb{R}^{C \times C}$  then project these tokens into query, key, and value representations

$$\mathbf{Q} = \mathbf{X}_{\text{token}} \mathbf{W}_O \tag{22}$$

$$\mathbf{K} = \mathbf{X}_{\text{token}} \mathbf{W}_K \tag{23}$$

$$\mathbf{V} = \mathbf{X}_{\text{token}} \mathbf{W}_{V}. \tag{24}$$

The multihead attention mechanism processes the generated Q, K, and V matrices through n parallel attention heads to model spectral relationships. This operation is expressed as follows:

$$\mathbf{A}_{i}^{\text{spectral}} = \text{Softmax} \left( \mu_{i} \mathbf{Q}_{i} \mathbf{K}_{i}^{\top} \right) \tag{25}$$

$$\mathbf{Output}_i = \mathbf{A}_i^{\text{spectral}} \mathbf{V}_i \tag{26}$$

$$S-MSA(\mathbf{X}_{token}) = Cat_{head}^{i}(\mathbf{Output}_{i})\mathbf{W} + PE(\mathbf{V})$$
 (27)

where  $\mathbf{A} \in \mathbb{R}^{HW \times HW}$  represents the attention score matrix,  $\mu_i$  is a learnable parameter,  $\mathbf{W} \in \mathbb{R}^{C \times C}$  is a learnable projection matrix used to project the concatenated outputs of all heads back to the original feature dimensionality,  $\mathrm{PE}(\cdot)$  represents positional encoding, which incorporates positional information into the features, and  $\mathrm{S-MSA}(\mathbf{x}_{\mathrm{token}}) \in \mathbb{R}^{HW \times C}$  is the final output.

As shown in Fig. 3(b), the input feature map is spatially divided into multiple windows, each containing  $M \times M$  pixels. In the SAB module, each window is treated as a token.

Before being processed, the input feature map is reshaped to  $\mathbf{x}'_{\text{token}} \in \mathbb{R}^{(HW/M^2) \times M^2 \times C}$ . The number of windows for W-MSA and SW-MSA is set to eight, with four shifted windows applied in SW-MSA. Other steps follow those in the SEB and are omitted for brevity.

### D. Reconstruction Block

For the reconstruction module, considering that the inputs of MSEB and RMSEB are the sequential spectral feature map  $\mathbf{F}_{\text{Vim}}$  and the reverse-order spectral feature map  $\mathbf{F}_{\text{Vim}(R)}$ , respectively, we propose to enable the network with dynamic merging capabilities for mutually supplementary frequency components present in the dual-branch outputs  $\mathbf{F}_{\text{SEB}_5}$  and  $\mathbf{F}_{\text{RSEB}_5}$ . Given the well-known bidirectional propagation capability and global attention of Vision Mamba, as well as the spectral and spatial attention mechanisms provided by CBAM, we incorporate both Vision Mamba and CBAM into the reconstruction module. The proposed mechanism achieves adaptive weighting on salient feature regions through attention allocation, enabling enhanced feature integration and texture recovery.

### E. Loss Function

To guarantee spectral–spatial fidelity in hyperspectral reconstruction, we adopt an  $\ell_1$ -norm-based regularization in the objective function. This loss encourages the network to minimize the absolute differences between the predicted and ground truth HSI, effectively preserving fine-grained spectral and spatial details. Additionally, within the MSAB, a separate  $L_1$  reconstruction loss is applied to ensure the precision of spatial information extracted from the RGB input. By optimizing this independent loss, the MSAB can focus on accurately modeling spatial features while simultaneously supporting the spectral reconstruction process. The following equations can express this process:

$$L_{\text{HSI}} = L_1(\mathbf{Y}, \hat{\mathbf{Y}}) \tag{28}$$

$$L_{\text{RGB}} = L_1(\mathbf{X}, \hat{\mathbf{X}}) \tag{29}$$

$$L_{\text{Finall}} = \alpha L_{\text{HSI}} + \beta L_{\text{RGB}} \tag{30}$$

where  $\alpha$  and  $\beta$  are trade-off weights.

# IV. EXPERIMENTS

### A. Datasets

Three hyperspectral datasets were utilized in our experimental framework: ICVL contains 201 images with 31 spectral channels each, where 184 samples were allocated for training and nine for testing. DFC2018 Houston provides 50 spectral channels, with 92 images randomly assigned to the training subset and six reserved for testing. TG1HRSSC integrates three modalities: panchromatic data, visible near-infrared with 54 spectral channels, and short-wave infrared with 52 spectral channels. Our experiment adopted the visible near-infrared modality, partitioning 40 images for training and six for test evaluation.

<!-- Page 7 -->

TABLE I FINAL TESTING RESULTS OF ICVL, DFC2018 HOUSTON, AND TG1HRSSC. THE BEST AND SECOND-BEST RESULTS ARE BOLD AND UNDERLINED, RESPECTIVELY. ↑ THE HIGHER THE BETTER, AND VICE VERSA

| Dataset         | Metric | Stat             | Ours                   | LTRN                | FSDFF              | SSRNet                  | MST++              | MSFN                      | HSRNet               | HSACS                     | AWAN               |
|-----------------|--------|------------------|------------------------|---------------------|--------------------|-------------------------|--------------------|---------------------------|----------------------|---------------------------|--------------------|
| ICVL            | PSNR↑  | Mean<br>Variance | <b>29.5380</b> 23.1087 | 28.1896<br>19.4280  | 28.9543 $27.1662$  | 29.1559<br>22.3426      | 29.1772<br>23.8839 | 29.0833<br>23.6635        | 29.2239<br>23.5852   | $\frac{29.4291}{22.4231}$ | 28.6324<br>19.3469 |
|                 | SSIM↑  | Mean<br>Variance | <b>0.8721</b> 0.0060   | 0.8680<br>0.0009    | 0.8311 $0.0072$    | 0.8699<br>0.0069        | $0.8693 \\ 0.0067$ | $0.8652 \\ 0.0073$        | $0.8618 \\ 0.0076$   | $\frac{0.8718}{0.0063}$   | $0.8421 \\ 0.0082$ |
|                 | SAM↓   | Mean<br>Variance | <b>7.0733</b> 5.8230   | 7.7747<br>3.7637    | 7.8401<br>6.7925   | 7.3821 $6.3153$         | 7.3895 $6.9263$    | 7.5215 $7.6693$           | 7.3656<br>6.8080     | $\frac{7.1797}{6.1934}$   | 7.7500 $5.1923$    |
| DFC2018 Houston | PSNR↑  | Mean<br>Variance | <b>31.4634</b> 3.3000  | 25.3134<br>2.0939   | 27.4312<br>1.0006  | 26.5621<br>2.4642       | 29.5294<br>7.0655  | $\frac{30.1771}{2.9224}$  | 28.5730<br>5.1888    | 29.8760<br>7.9936         | 29.9709<br>4.1075  |
|                 | SSIM↑  | Mean<br>Variance | <b>0.9501</b> 0.0001   | $0.8298 \\ 0.0005$  | 0.8688<br>0.0001   | $0.9409 \\ 0.00002$     | $0.9416 \\ 0.0001$ | 0.9418 $0.00002$          | 0.9104<br>0.0008     | $\frac{0.9486}{0.00004}$  | 0.9468 $0.00002$   |
|                 | SAM↓   | Mean<br>Variance | <b>7.3471</b> 2.8188   | $14.7681 \\ 6.5268$ | 11.4101<br>2.5848  | $12.0027 \\ 1.7673$     | $9.0179 \\ 5.5463$ | 8.5957 $2.9160$           | $10.4958 \\ 10.5601$ | $\frac{8.3038}{5.1200}$   | 8.7143<br>3.7330   |
| TG1HRSSC        | PSNR↑  | Mean<br>Variance | <b>28.6264</b> 19.7263 | 27.8362<br>10.3274  | 24.8606<br>31.0648 | 26.9268<br>30.3795      | 28.3167<br>20.7677 | $\frac{28.4690}{24.2254}$ | 27.0887<br>26.3734   | 27.8440<br>18.3620        | 27.0703<br>47.7623 |
|                 | SSIM↑  | Mean<br>Variance | <b>0.9091</b> 0.0010   | 0.8930<br>0.0018    | $0.8135 \\ 0.0020$ | $\frac{0.9064}{0.0016}$ | $0.8718 \\ 0.0043$ | $0.8954 \\ 0.0021$        | $0.8896 \\ 0.0003$   | $0.8940 \\ 0.0023$        | $0.8806 \\ 0.0027$ |
|                 | SAM↓   | Mean<br>Variance | <b>6.0575</b> 1.5945   | 6.8895<br>4.7996    | $9.3378 \\ 4.2879$ | 7.3815 $4.4295$         | 6.3581<br>1.0066   | 6.1298<br>0.9963          | 7.3842 $4.6580$      | $6.5715 \\ 0.6961$        | 7.9552 $15.2375$   |

Fig. 4. ICVL dataset evaluation displays comparative results across nine methodologies. Odd-numbered rows present HSI reconstructions visualized through pseudo-coloration, while even-numbered rows employ chromatic error gradients to quantify spectral reconstruction fidelity. Cooler hues in error distributions correspond to minimized spectral angle deviations between reconstructed and reference data.

TABLE II ABLATION STUDY RESULTS ON THE TG1HRSSC DATASET SHOW HOW DIFFERENT MODEL DESIGNS PERFORM. THE TOP TWO BEST SCORES ARE BOLD AND UNDERLINED, RESPECTIVELY. ↑ THE HIGHER THE BETTER, AND VICE VERSA

| Mode  | el RMSEB     | Weight Share | Reconstruction | $L_{RGB}$    | PSNR↑               | SSIM↑  | SAM↓   |
|-------|--------------|--------------|----------------|--------------|---------------------|--------|--------|
| 1     | ×            | ✓            | ✓              | ✓            | 27.9682             | 0.8951 | 6.5189 |
| 2     | $\checkmark$ | ×            | $\checkmark$   | $\checkmark$ | $\frac{-}{26.6399}$ | 0.9065 | 7.3411 |
| 3     | $\checkmark$ | $\checkmark$ | X              | $\checkmark$ | 26.5343             | 0.8862 | 8.0959 |
| 4     | $\checkmark$ | $\checkmark$ | $\checkmark$   | X            | 26.1646             | 0.8755 | 8.6879 |
| BiSAN | Net ✓        | $\checkmark$ | $\checkmark$   | $\checkmark$ | 28.6264             | 0.9091 | 6.0575 |

## *B. Experimental Settings*

*Evaluation metrics:* Three principal evaluation criteria were adopted for objective performance benchmarking across methodologies: peak signal-to-noise ratio (PSNR) assessing reconstruction fidelity, structural similarity index (SSIM) quantifying image quality preservation, and spectral angle

<!-- Page 8 -->

Fig. 5. DFC2018 Houston dataset evaluation displays comparative results across nine methodologies. Odd-numbered rows present HSI reconstructions visualized through pseudo-coloration, while even-numbered rows employ chromatic error gradients to quantify spectral reconstruction fidelity. Cooler hues in error distributions correspond to minimized spectral angle deviations between reconstructed and reference data.

Fig. 6. TG1HRSSC dataset evaluation displays comparative results across nine methodologies. Odd-numbered rows present HSI reconstructions visualized through pseudo-coloration, while even-numbered rows employ chromatic error gradients to quantify spectral reconstruction fidelity. Cooler hues in error distributions correspond to minimized spectral angle deviations between reconstructed and reference data.

mapper (SAM) verifying spectral accuracy. These standardized metrics constitute the prevailing evaluation paradigm in HSI processing research, systematically addressing spatial, structural, and spectral dimension validations

$$MSE = \frac{1}{N} \sum_{i=0}^{N} ||x_i - y_i||^2$$
 (31)

$$PSNR = 10 \cdot \log_{10} \left( \frac{MAX_I^2}{MSE} \right)$$
 (32)

where  $MAX_I^2$  denotes the maximum attainable squared pixel intensity value. For instance, when employing 8-bit image representation (2<sup>8</sup> quantization levels),  $MAX_I$  adopts the standard

value of 255. The variables  $x_i$  and  $y_i$  correspond to paired pixel intensities from the compared image pair, while N quantifies the total pixel count in both images under comparison

SSIM = 
$$\frac{(2\mu_x \mu_y + c_1)(\sigma_{xy} + c_2)}{(\mu_x^2 + \mu_y^2 + c_1)(\sigma_x^2 + \sigma_y^2 + c_2)}$$
(33)

where  $\mu_x$  and  $\mu_y$  denote the mean intensity values of compared images x and y, respectively,  $\sigma_x^2$ ,  $\sigma_y^2$  represent their variance measures, and  $\sigma_{xy}$  quantifies cross-image covariance. The parameters  $c_1$  and  $c_2$  are stabilization coefficients introduced to prevent division-by-zero anomalies in numerical

<!-- Page 9 -->

Fig. 7. Spectral curves of randomly picked pixels from HSIs reconstructed by the compared methods. (a)–(c) Spectral curves are derived from test set images partitioned from the ICVL, DFC2018 Houston, and TG1HRSSC datasets, respectively.

Fig. 8. PSNR trends of nine methods for testing images on three datasets: ICVL, DFC2018 Houston, and TG1HRSSC. The horizontal axis represents the PSNR value, while the vertical axis indicates the image index.

computation

$$SAM = \frac{1}{N} \sum_{i=1}^{N} \arccos\left(\frac{x_i^{\mathsf{T}} y_i}{\|x_i\| \|y_i\|}\right)$$
(34)

where *N* is the number of pixels of *x* and *y*.

## *C. Implementation Details*

BiSANet is implemented based on the PyTorch framework. All experiments are performed on a system equipped with an NVIDIA RTX 3090. The trade-off weight of the loss function is set to α = 0.5 and β = 0.5. The initial learning rate, batch size, and epoch are set to 1e<sup>−</sup><sup>4</sup> , 8, and 200. Adam was chosen as the network optimizer. The train datasets are cropped into image patches of size 64 × 64 × 3, and the test datasets are cropped into 256 × 256 × 3.

## *D. Main Results*

The proposed network was evaluated against eight advanced SSR architectures covering diverse methodology innovations: LTRN [25], FSDFF [64], SSRNet [19], MST++ [24], MSFN [20], HSRNet [22], HSACS [21], and AWAN [23].

*1) Qualitative Results:* Visual analysis across three benchmark datasets is presented in Figs. 4–6. The odd-numbered rows showcase pseudo-color representations derived from hyperspectral data, whereas even-numbered rows visualize spectral angle mapping errors through chromatic error distributions. This comparative visualization effectively contrasts reconstructed spectral information with corresponding spatial error patterns. In the error maps, blue areas indicate smaller errors, whereas red areas signify larger errors. From the visualizations, it is evident that our network produces highquality pseudo-color images closely matching the ground truth, while other methods often exhibit issues such as color distortion or overall blurring, especially in detailed and edge regions. The error map comparisons demonstrate that the proposed method achieves superior error control capability across various regions compared to six mainstream SSR methods, particularly maintaining accurate spectral reconstruction in geometrically complex areas. These advantages are attributed to the bidirectional spectral attention modeling and multilevel spectral–spatial information fusion within our network, enabling comprehensive and accurate spectral–spatial information integration and resulting in outstanding reconstruction performance. To verify our network's performance, reconstructed HSI spectral curves were plotted at randomly sampled pixel locations and compared alongside ground-truth references. As illustrated in Fig. 7, the spectral profiles produced by our BiSANet demonstrate strong agreement with ground-truth measurements across all evaluated SSR methodologies. Our method accurately captures the major spectral characteristics and closely aligns with the ground truth in finer spectral details. These findings further confirm our network's powerful performance and reliability in SSR tasks.

<!-- Page 10 -->

TABLE III COMPARISON OF TRAINING TIMES, TESTING TIMES, AND NUMBER OF PARAMETERS OF NINE METHODS ON THE TG1HRSSC DATASET. THE BEST RESULTS ARE SET TO BOLD

| TG1HRSSC                                | Ours         | LTRN    | FSDFF  | SSRNet       | MST++  | MSFN   | HSRNet       | HSACS  | AWAN   |
|-----------------------------------------|--------------|---------|--------|--------------|--------|--------|--------------|--------|--------|
| Train Times Test Times Parameter amount | 11.19s       | 270.54s | 32.35s | 8.14s        | 12.64s | 18.64s | <b>8.03s</b> | 42.35s | 8.84s  |
|                                         | 0.98s        | 1.44s   | 0.96s  | <b>0.48s</b> | 1.13s  | 1.23s  | 0.50s        | 0.96s  | 0.76s  |
|                                         | <b>0.30M</b> | 5.19M   | 17.33M | 0.39M        | 1.62M  | 2.47M  | 0.77M        | 19.74M | 21.63M |

*2) Quantitative Results:* As shown in Table I, we compare the performance using three selected metrics, which represent the average values tested on the dataset. The top-performing instance is emphasized in bold, and the second-best is distinctively marked in underlined, reflecting their premier standings in the evaluation metrics. Our BiSANet consistently outperforms the compared SSR methods across all three datasets, demonstrating its strong competitiveness. As evident from Table I, while the variances of the nine methods across the three datasets are relatively close, Fig. 8 further illustrates that, regardless of such variance fluctuations, our proposed method consistently outperforms the other eight methods in PSNR for all three datasets. On the ICVL dataset, it achieves a 0.37% increase in PSNR, 0.03% improvement in SSIM, and 1.48% reduction in SAM compared to the second-best approach. For the DFC2018 Houston dataset, the method shows more significant advantages with 4.26% higher PSNR, 0.16% better SSIM, and 11.52% lower SAM than the runner up method. For the TG1HRSSC dataset, the improvements are 0.55% in PSNR, 0.30% in SSIM, and 1.18% lower SAM. The significant advantages in PSNR and SAM demonstrate the outstanding performance of our network in spectral information recovery. This exceptional capability is primarily attributed to several innovative designs in our network. First, bidirectional spectral attention modeling allows for the comprehensive capture of correlations in the spectral dimension, enabling more precise restoration of spectral features. Furthermore, the integration of independent spatial loss modeling provides additional supervisory signals from the spatial dimension, further enhancing the network's ability to recover spectral information. Additionally, the multilevel fusion mechanism of spectral and spatial information plays a crucial role. By progressively fusing spectral and spatial features at different scales, this mechanism strengthens the synergy between spectral and spatial information. Such a design not only improves the accuracy of spectral recovery but also significantly enhances the network's adaptability to complex scenarios and fine details, ultimately achieving efficient interaction and precise modeling of spectral and spatial information.

## *E. Ablation Analysis*

We designed four BiSANet variants to test our proposed components' effectiveness.

*Variant 1:* To evaluate the importance of bidirectional spectral attention modeling, we removed the RMSEB module and replaced it with MSEB, making both spectral branches process input feature maps in the same sequential spectral order. As shown in Table II, PSNR and SSIM decreased by 2.30% and 1.54%, respectively, while SAM increased by 7.62%. These results demonstrate that bidirectional spectral attention modeling enables more efficient spectral information capture.

*Variant 2:* To test the significance of weight sharing between MSEB and RMSEB, we removed the shared weights and trained the two spectral branches independently. Table II shows that PSNR and SSIM decreased by 6.94% and 0.29%, respectively, while SAM increased by 7.62%. This suggests the two spectral attention branches extract complementary, not conflicting, spectral information. Joint training enables more effective and accurate spectral information extraction.

*Variant 3:* To evaluate the reconstruction module's performance, we substituted it with a ResNet-based architecture. As shown in Table II, PSNR and SSIM dropped by 7.31% and 2.52%, respectively, while SAM increased by 33.65%. This performance gap highlights the superiority of our reconstruction module, attributed to the integration of Vision Mamba for global information modeling and adaptive bidirectional spectral information fusion. Additionally, CBAM facilitates attention extraction and fusion in both spectral and spatial dimensions, achieving highly accurate reconstruction results.

*Variant 4:* To test the effectiveness of the independent reconstruction loss in MSAB, we removed *L*RGB. As shown in Table II, PSNR and SSIM decreased by 8.60% and 3.70%, respectively, while SAM increased by 43.42%. These results reveal the importance of precise spatial information for spectral information acquisition and HSI reconstruction. By incorporating multilevel spatial information injection and independent reconstruction loss, our network efficiently extracts and integrates spatial information, laying a solid foundation for subsequent HSI reconstruction.

From the above ablation experiments, it is evident that our network effectively captures spectral information. Accurate spatial information integration and effective spectral–spatial fusion enable our network to achieve state-of-the-art HSI reconstruction results.

## *F. Training and Inference Efficiency*

Regarding training and inference efficiency, as shown in Table III, BiSANet demonstrates notable advantages. With a training time of 11.19 s, it operates slightly slower than ultra-lightweight models such as SSRNet and HSRNet while being substantially faster than complex architectures like LTRN and FSDFF. This efficiency is primarily attributed to the linear-complexity computation of the Vision Mamba module and the collaborative optimization of bidirectional attention mechanisms, enabling efficient feature extraction

<!-- Page 11 -->

while mitigating excessive training consumption. For inference, BiSANet achieves a testing speed of 0.98 s. Despite the computational overhead from multibranch feature fusion, it leverages an ultra-lightweight parameter count of only 0.3 M—a 23.1% reduction compared to the second-best methods and a 98.6% reduction versus AWAN. Through efficient interaction mechanisms, including bidirectional spectral attention and multistage spatial information injection, the model achieves an excellent balance between performance and efficiency. Importantly, BiSANet exhibits significant reconstruction accuracy advantages across three benchmark datasets, underscoring its superiority in practical applications requiring both high precision and computational efficiency.

## V. CONCLUSION

In this article, we present a novel deep learning framework, BiSANet, designed to tackle the challenging task of HSI reconstruction. Inspired by video super-resolution techniques, our network pioneers the concept of bidirectional spectral attention modeling. Through the integration of MSEB and RMSEB modules, BiSANet effectively captures complementary spectral information. The reconstruction module leverages the strengths of Vision Mamba and CBAM, enabling adaptive fusion of spectral and spatial features. Furthermore, the MSAB combined with an independent reconstruction loss significantly improves spatial feature extraction, delivering essential spatial context information for accurate and high-quality HSI reconstruction. Comprehensive testing across three open-access datasets confirms our network's superior performance compared to existing SSR techniques in both quantitative and qualitative experiments. However, BiSANet's reliance on paired RGB-HSI training data limits its applicability to unlabeled scenarios. Future work could focus on semi-supervised or self-supervised learning to leverage unlabeled data, reducing data dependency while improving generalization. Additionally, exploring lightweight architectures to enhance real-time deployment efficiency and addressing long-range spectral correlations in high-dimensional hyperspectral data represent promising directions for further optimization.

## REFERENCES

- [1] J. M. Bioucas-Dias, A. Plaza, G. Camps-Valls, P. Scheunders, N. Nasrabadi, and J. Chanussot, "Hyperspectral remote sensing data analysis and future challenges," *IEEE Geosci. Remote Sens. Mag.*, vol. 1, no. 2, pp. 6–36, Jun. 2013.
- [2] R. Dian, S. Li, B. Sun, and A. Guo, "Recent advances and new guidelines on hyperspectral and multispectral image fusion," *Inf. Fusion*, vol. 69, pp. 40–51, May 2021.
- [3] L. Zhang, J. Nie, W. Wei, Y. Li, and Y. Zhang, "Deep blind hyperspectral image super-resolution," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 32, no. 6, pp. 2388–2400, Jun. 2021.
- [4] W. Wang et al., "Enhanced deep blind hyperspectral image fusion," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 34, no. 3, pp. 1513–1523, Mar. 2023.
- [5] J. Li, Z. Zhang, R. Song, Y. Li, and Q. Du, "SCFormer: Spectral coordinate transformer for cross-domain few-shot hyperspectral image classification," *IEEE Trans. Image Process.*, vol. 33, pp. 840–855, 2024.
- [6] J. Li, Y. Liu, R. Song, Y. Li, K. Han, and Q. Du, "Sal2RN: A spatial–spectral salient reinforcement network for hyperspectral and LiDAR data fusion classification," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, 2022, Art. no. 5500114.

- [7] H. Pu, L. Lin, and D.-W. Sun, "Principles of hyperspectral microscope imaging techniques and their applications in food quality and safety detection: A review," *Comprehensive Rev. Food Sci. Food Saf.*, vol. 18, no. 4, pp. 853–866, Jul. 2019.
- [8] A. A. Gowen, C. P. O'Donnell, P. J. Cullen, G. Downey, and J. M. Frias, "Hyperspectral imaging—An emerging process analytical tool for food quality and safety control," *Trends Food Sci. Technol.*, vol. 18, no. 12, pp. 590–598, 2007.
- [9] Y. Wang, Q. Yuan, T. Li, and L. Zhu, "Global spatiotemporal estimation of daily high-resolution surface carbon monoxide concentrations using deep forest," *J. Cleaner Prod.*, vol. 350, May 2022, Art. no. 131500.
- [10] Y. Wang, Q. Yuan, S. Zhou, and L. Zhang, "Global spatiotemporal completion of daily high-resolution TCCO from TROPOMI over land using a swath-based local ensemble learning method," *ISPRS J. Photogramm. Remote Sens.*, vol. 194, pp. 167–180, Dec. 2022.
- [11] S. Salcedo-Sanz et al., "Machine learning information fusion in Earth observation: A comprehensive review of methods, applications and data sources," *Inf. Fusion*, vol. 63, pp. 256–272, Nov. 2020.
- [12] F. D. van der Meer et al., "Multi-and hyperspectral geologic remote sensing: A review," *Int. J. Appl. Earth Observ. Geoinf.*, vol. 14, no. 1, pp. 112–128, Feb. 2012.
- [13] Y. Wang, Q. Yuan, T. Li, L. Zhu, and L. Zhang, "Estimating daily full-coverage near surface O3, CO, and NO<sup>2</sup> concentrations at a high spatial resolution over China based on S5P-TROPOMI and GEOS-FP," *ISPRS J. Photogramm. Remote Sens.*, vol. 175, pp. 311–325, May 2021.
- [14] M. Descour and E. Dereniak, "Computed-tomography imaging spectrometer: Experimental calibration and reconstruction results," *Appl. Opt.*, vol. 34, no. 22, pp. 4817–4826, 1995.
- [15] H. Kwon and Y.-W. Tai, "RGB-guided hyperspectral image upsampling," in *Proc. IEEE Int. Conf. Comput. Vis. (ICCV)*, Dec. 2015, pp. 307–315.
- [16] X. Cao, H. Du, X. Tong, Q. Dai, and S. Lin, "A prism-mask system for multispectral video acquisition," *IEEE Trans. Pattern Anal. Mach. Intell.*, vol. 33, no. 12, pp. 2423–2435, Dec. 2011.
- [17] T. Akgun, Y. Altunbasak, and R. M. Mersereau, "Super-resolution reconstruction of hyperspectral images," *IEEE Trans. Image Process.*, vol. 14, no. 11, pp. 1860–1875, Nov. 2005.
- [18] S. Gou, S. Liu, S. Yang, and L. Jiao, "Remote sensing image super-resolution reconstruction based on nonlocal pairwise dictionaries and double regularization," *IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens.*, vol. 7, no. 12, pp. 4784–4792, Dec. 2014.
- [19] R. Dian, T. Shan, W. He, and H. Liu, "Spectral super-resolution via model-guided cross-fusion network," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 35, no. 7, pp. 10059–10070, Jul. 2024.
- [20] Y. Wu, R. Dian, and S. Li, "Multistage spatial–spectral fusion network for spectral super-resolution," *IEEE Trans. Neural Netw. Learn. Syst.*, pp. 1–11, 2024, doi: [10.1109/TNNLS.2024.3460190.](http://dx.doi.org/10.1109/TNNLS.2024.3460190)
- [21] J. Li et al., "Deep hybrid 2-D–3-D CNN based on dual second-order attention with camera spectral sensitivity prior for spectral superresolution," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 34, no. 2, pp. 623–634, Feb. 2023.
- [22] J. He, J. Li, Q. Yuan, H. Shen, and L. Zhang, "Spectral response function-guided deep optimization-driven network for spectral superresolution," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 33, no. 9, pp. 4213–4227, Sep. 2022.
- [23] J. Li, C. Wu, R. Song, Y. Li, and F. Liu, "Adaptive weighted attention network with camera spectral sensitivity prior for spectral reconstruction from RGB images," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW)*, Jun. 2020, pp. 462–463.
- [24] Y. Cai et al., "MST++: Multi-stage spectral-wise transformer for efficient spectral reconstruction," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW)*, Jun. 2022, pp. 745–755.
- [25] R. Dian, Y. Liu, and S. Li, "Spectral super-resolution via deep low-rank tensor representation," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 36, no. 3, pp. 5140–5150, Mar. 2025.
- [26] J. Li, Y. Leng, R. Song, W. Liu, Y. Li, and Q. Du, "MFormer: Taming masked transformer for unsupervised spectral reconstruction," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, 2023, Art. no. 5508412.
- [27] X. Han, H. Zhang, J.-H. Xue, and W. Sun, "A spectral–spatial jointed spectral super-resolution and its application to HJ-1A satellite images," *IEEE Geosci. Remote Sens. Lett.*, vol. 19, pp. 1–5, 2022.
- [28] Y. Baran Can and R. Timofte, "An efficient CNN for spectral reconstruction from RGB images," 2018, *arXiv:1804.04647*.
- [29] J. Li, K. Zheng, L. Gao, Z. Han, Z. Li, and J. Chanussot, "Enhanced deep image prior for unsupervised hyperspectral image super-resolution," *IEEE Trans. Geosci. Remote Sens.*, vol. 63, 2025, Art. no. 5504218.

<!-- Page 12 -->

- [30] R. Dian, Y. Liu, and S. Li, "Hyperspectral image fusion via a novel generalized tensor nuclear norm regularization," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 36, no. 4, pp. 7437–7448, Apr. 2025.
- [31] Y. Liu, R. Dian, and S. Li, "Low-rank transformer for high-resolution hyperspectral computational imaging," *Int. J. Comput. Vis.*, vol. 133, no. 2, pp. 809–824, Feb. 2025.
- [32] R. Dian, A. Guo, and S. Li, "Zero-shot hyperspectral sharpening," *IEEE Trans. Pattern Anal. Mach. Intell.*, vol. 45, no. 10, pp. 12650–12666, Oct. 2023.
- [33] K. C. K. Chan, X. Wang, K. Yu, C. Dong, and C. C. Loy, "BasicVSR: The search for essential components in video super-resolution and beyond," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2021, pp. 4947–4956.
- [34] Y. Xiao et al., "Local-global temporal difference learning for satellite video super-resolution," *IEEE Trans. Circuits Syst. Video Technol.*, vol. 34, no. 4, pp. 2789–2802, Apr. 2024.
- [35] Z. Liu et al., "Swin transformer: Hierarchical vision transformer using shifted windows," in *Proc. IEEE/CVF Int. Conf. Comput. Vis. (ICCV)*, Oct. 2021, pp. 10012–10022.
- [36] Y. Xiao, Q. Yuan, K. Jiang, Y. Chen, Q. Zhang, and C.-W. Lin, "Frequency-assisted mamba for remote sensing image super-resolution," *IEEE Trans. Multimedia*, vol. 27, pp. 1783–1796, 2025.
- [37] L. Zhu, B. Liao, Q. Zhang, X. Wang, W. Liu, and X. Wang, "Vision mamba: Efficient visual representation learning with bidirectional state space model," 2024, *arXiv:2401.09417*.
- [38] S. Woo, J. Park, J.-Y. Lee, and I. S. Kweon, "CBAM: Convolutional block attention module," in *Proc. Eur. Conf. Comput. Vis. (ECCV)*, Sep. 2018, pp. 3–19.
- [39] M. Breuer and J. Albertz, "Geometric correction of airborne whiskbroom scanner imagery using hybrid auxiliary data," *Int. Arch. Photogramm. Remote Sens.*, vol. 33, pp. 93–100, Jan. 2000.
- [40] D. Poli and T. Toutin, "Review of developments in geometric modelling for high resolution satellite pushbroom sensors," *Photogramm. Rec.*, vol. 27, no. 137, pp. 58–73, Mar. 2012.
- [41] X. Cao et al., "Computational snapshot multispectral cameras: Toward dynamic capture of the spectral world," *IEEE Signal Process. Mag.*, vol. 33, no. 5, pp. 95–108, Sep. 2016.
- [42] H. Du, X. Tong, X. Cao, and S. Lin, "A Prism-based system for multispectral video acquisition," in *Proc. IEEE 12th Int. Conf. Comput. Vis. (ICCV)*, Sep./Oct. 2009, pp. 175–182.
- [43] A. A. Wagadarikar, N. P. Pitsianis, X. Sun, and D. J. Brady, "Video rate spectral imaging using a coded aperture snapshot spectral imager," *Opt. Exp.*, vol. 17, no. 8, pp. 6368–6388, 2009.
- [44] Y. Cai, X. Hu, H. Wang, Y. Zhang, H. Pfister, and D. Wei, "Learning to generate realistic noisy images via pixel-level noise-aware adversarial training," in *Proc. Adv. Neural Inf. Process. Syst.*, vol. 34, 2021, pp. 3259–3270.
- [45] Y. Cai et al., "Mask-guided spectral-wise transformer for efficient hyperspectral image reconstruction," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2022, pp. 17502–17511.
- [46] X. Hu et al., "HDNet: High-resolution dual-domain learning for spectral compressive imaging," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit.*, Oct. 2022, pp. 17542–17551.
- [47] T. Huang, W. Dong, X. Yuan, J. Wu, and G. Shi, "Deep Gaussian scale mixture prior for spectral compressive imaging," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit.*, Jun. 2021, pp. 16216–16225.
- [48] Y. Cai et al., "Coarse-to-fine sparse transformer for hyperspectral image reconstruction," in *Proc. Eur. Conf. Comput. Vis. (ECCV)*. Switzerland: Springer, 2022, pp. 686–704.
- [49] L. Wang, C. Sun, Y. Fu, M. H. Kim, and H. Huang, "Hyperspectral image reconstruction using a deep spatial–spectral prior," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2019, pp. 8032–8041.
- [50] Z. Meng, J. Ma, and X. Yuan, "End-to-end low cost compressive spectral imaging with spatial–spectral self-attention," in *Proc. Eur. Conf. Comput. Vis. (ECCV)*. Springer, 2020, pp. 187–204.
- [51] Z. Xiong, Z. Shi, H. Li, L. Wang, D. Liu, and F. Wu, "HSCNN: CNN-based hyperspectral image recovery from spectrally undersampled projections," in *Proc. IEEE Int. Conf. Comput. Vis. Workshops (ICCVW)*, Oct. 2017, pp. 518–525.
- [52] Z. Shi, C. Chen, Z. Xiong, D. Liu, and F. Wu, "HSCNN+: Advanced CNN-based hyperspectral recovery from RGB images," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW)*, Jun. 2018, pp. 1052–10528.

- [53] B. Arad et al., "NTIRE 2018 challenge on spectral reconstruction from RGB images," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW)*, Jun. 2018, pp. 1042–104209.
- [54] T. Stiebel, S. Koppers, P. Seltsam, and D. Merhof, "Reconstructing spectral images from RGB-images using a convolutional neural network," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW)*, Jun. 2018, pp. 1061–10615.
- [55] A. Vaswani et al., "Attention is all you need," in *Proc. Adv. Neural Inf. Process. Syst.*, vol. 30, 2017, pp. 1–9.
- [56] J. Hu, L. Shen, and G. Sun, "Squeeze-and-excitation networks," in *Proc. IEEE Conf. Comput. Vis. Pattern Recognit.*, Jul. 2018, pp. 7132–7141.
- [57] L. Gao, J. Li, K. Zheng, and X. Jia, "Enhanced autoencoders with attention-embedded degradation learning for unsupervised hyperspectral image super-resolution," *IEEE Trans. Geosci. Remote Sens.*, vol. 61, 2023, Art. no. 5509417.
- [58] Y. Xiao, Q. Yuan, K. Jiang, J. He, C.-W. Lin, and L. Zhang, "TTST: A top-k token selective transformer for remote sensing image superresolution," *IEEE Trans. Image Process.*, vol. 33, pp. 738–752, 2024.
- [59] H. Peng, X. Chen, and J. Zhao, "Residual pixel attention network for spectral reconstruction from RGB images," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW)*, Jun. 2020, pp. 2012–2020.
- [60] A. Dosovitskiy et al., "An image is worth 16×16 words: Transformers for image recognition at scale," 2020, *arXiv:2010.11929*.
- [61] Y. Cai et al., "Degradation-aware unfolding half-shuffle transformer for spectral compressive imaging," in *Proc. Adv. Neural. Inf. Process. Syst.*, vol. 35, 2022, pp. 37749–37761.
- [62] K. Jiang et al., "Multi-scale progressive fusion network for single image deraining," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR)*, Jun. 2020, pp. 8343–8352.
- [63] K. Jiang et al., "Multi-scale hybrid fusion network for single image deraining," *IEEE Trans. Neural Netw. Learn. Syst.*, vol. 34, no. 7, pp. 3594–3608, Jul. 2023.
- [64] L. Tan, R. Dian, S. Li, and J. Liu, "Frequency-spatial domain feature fusion for spectral super-resolution," *IEEE Trans. Comput. Imag.*, vol. 10, pp. 589–599, 2024.

Xintao Zhong received the B.S. degree from Zhuhai College, Jilin University, Zhuhai, China, in 2023. He is currently pursuing the master's degree with Ningbo University, Ningbo, China.

His research interests include spectral superresolution (SSR).

Shenfu Zhang received the B.S. degree from Shaoxing University, Shaoxing, China, in 2022. He is currently pursuing the Ph.D. degree with Ningbo University, Ningbo, China.

His research interests include hyperspectral image processing and multisource data fusion classification.

<!-- Page 13 -->

Liang Chen received the B.S. and Ph.D. degrees from the University of Science and Technology of China, Hefei, China, in 2016 and 2023, respectively.

He is currently a Lecturer with the Faculty of Electrical Engineering and Computer Science, Ningbo University, Ningbo, China. His research interests include hyperspectral image processing and target detection.

Gang Yang received the M.S. degree in geographical information system from Hunan University of Science and Technology, Xiangtan, China, in 2012, and the Ph.D. degree from the School of Resource and Environmental Sciences, Wuhan University, Wuhan, China, in 2016.

He is currently an Associate Professor with Ningbo University, Ningbo, Zhejiang, China. His research interests include missing information reconstruction of remote sensing image, cloud removal of remote sensing image, and remote sensing time-series products temporal reconstruction.

Feng Shao (Senior Member, IEEE) received the B.S. and Ph.D. degrees from Zhejiang University, Hangzhou, China, in 2002 and 2007, respectively, all in electronic science and technology.

He was a Visiting Fellow with the School of Computer Engineering, Nanyang Technological University, Singapore, from February 2012 to August 2012. He is currently a Professor with the Faculty of Information Science and Engineering, Ningbo University, Ningbo, China. He has published over 100 technical articles in refereed journals and pro-

ceedings in the areas of 3-D video coding, 3-D quality assessment, and image perception.

Dr. Shao received the "Excellent Young Scholar" Award from the NSF of China (NSFC) in 2016.

Weiwei Sun (Senior Member, IEEE) received the B.S. degree in surveying and mapping and the Ph.D. degree in cartography and geographic information engineering from Tongji University, Shanghai, China, in 2007 and 2013, respectively.

From 2011 to 2012, he was with the Department of Applied Mathematics, University of Maryland, College Park, MD, USA, as a Visiting Scholar with the famous Prof. John Benedetto to study on the dimensionality reduction of Hyperspectral Image. From 2014 to 2016, he was with the State Key

Laboratory for Information Engineering in Surveying, Mapping and Remote Sensing (LIESMARS), Wuhan University, Wuhan, China, working as a Post-Doctoral Researcher to study intelligent processing in hyperspectral imagery. From 2017 to 2018, he was with the Department of Electrical and Computer Engineering, Mississippi State University, Starkville, MS, USA, and a Visiting Scholar in hyperspectral image processing. He is currently a Full Professor with Ningbo University, Ningbo, Zhejiang, China. He has published more than 80 journal articles. His research interests include hyperspectral image processing with machine learning.

Xiangchao Meng (Senior Member, IEEE) received the B.S. degree in geographic information system from Shandong University of Science and Technology, Qingdao, China, in 2012, and the Ph.D. degree in cartography and geography information system from Wuhan University, Wuhan, China, in 2017.

He was a Post-Doctoral Researcher with the College of Electrical and Information Engineering, Hunan University, Changsha, China. He is currently a Professor with the Faculty of Electrical Engineering and Computer Science, Ningbo University,

Ningbo, China. His research interests include multisource data fusion and machine learning.